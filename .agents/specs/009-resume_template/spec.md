# Sprint 009: Cover Letter Template Generation and Management

# Sprint Overview

## Goal
Extend the Templates page to support cover letter template generation and implement manual cover letter creation with versioning on the job detail page.

## Background
Currently, users can only create resumes for job applications. Cover letters are a critical part of job applications and need template-based support. This sprint adds parallel functionality for cover letters: AI-powered template generation on the Templates page and manual cover letter editing on the job detail page.

## Key Changes
1. Add tab structure to Templates page for Resume/Cover Letter separation
2. Create cover letter feature module (`src/features/cover_letter/`) with Pydantic models, template generation, and validation
3. Implement job detail cover letter tab for manual editing with versioning support
4. Update database schema: modify `CoverLetter` table to support structured JSON data and template references, add `CoverLetterVersion` table
5. Create `CoverLetterService` and `CoverLetterTemplateService` for business logic

## User Impact
- Users will be able to create professional cover letter templates via AI chat interface on the Templates page
- Users can manually fill in cover letters for specific job applications on the job detail page
- Cover letters support versioning: each save creates a new version, allowing users to track changes over time
- Cover letters are locked when a job is marked as Applied, maintaining a record of submitted content

---

# User Stories

1. **As a user**, I want to create custom cover letter templates using AI so that I can have multiple professional designs to choose from
   - **Acceptance**: User can describe a cover letter style in chat, receive generated template, iterate with feedback, and download the template

2. **As a user**, I want to manually fill in cover letter content for a job so that I can write personalized cover letters
   - **Acceptance**: User can enter name, email, phone, date, job title, and body paragraphs on the job cover letter tab

3. **As a user**, I want to see a live PDF preview of my cover letter so that I can ensure it looks professional before saving
   - **Acceptance**: PDF preview updates in real-time as user edits fields

4. **As a user**, I want to save multiple versions of my cover letter so that I can track changes and revert if needed
   - **Acceptance**: Each save creates a new version; user can navigate between versions using ◀ ▶ controls

5. **As a user**, I want my cover letter to be locked after applying to a job so that I maintain a record of what I submitted
   - **Acceptance**: When job.applied_at is set, all cover letter fields become read-only and editing is disabled

6. **As a user**, I want to download my final cover letter as a PDF so that I can submit it with my application
   - **Acceptance**: Download button generates PDF with proper filename format

---

# Data Models

## CoverLetter Table (Modified)

Update `CoverLetter` table in `src/database.py`:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int PK | Primary key |
| `job_id` | int FK | Foreign key to Job table |
| `cover_letter_json` | str | JSON string with structured cover letter data |
| `template_name` | str | Template filename (e.g., "cover_000.html") |
| `locked` | bool | Lock status (default False) |
| `created_at` | datetime | Creation timestamp |
| `updated_at` | datetime | Last update timestamp |

**Changes from current schema:**
- Remove `content: str` field
- Add `cover_letter_json: str` field
- Add `template_name: str` field (default "cover_000.html")

**Cover Letter JSON Structure:**
```json
{
  "name": "Candidate Name",
  "title": "Job Title",
  "email": "email@example.com",
  "phone": "555-1234",
  "date": "2025-10-07",
  "body_paragraphs": [
    "First paragraph expressing interest...",
    "Second paragraph highlighting relevant experience...",
    "Third paragraph closing statement...",
    "(optional 4th paragraph)"
  ]
}
```

## CoverLetterVersion Table (New)

Create new `CoverLetterVersion` table in `src/database.py` (similar to `ResumeVersion`):

| Field | Type | Description |
|-------|------|-------------|
| `id` | int PK | Primary key |
| `cover_letter_id` | int FK | Foreign key to CoverLetter table |
| `job_id` | int FK | Foreign key to Job table (for easier querying) |
| `version_index` | int | Version number (1, 2, 3...) |
| `cover_letter_json` | str | Snapshot of cover letter data at this version |
| `template_name` | str | Template used for this version |
| `created_by_user_id` | int | User who created this version |
| `created_at` | datetime | Creation timestamp |

**Notes:**
- The `CoverLetter` table acts as the canonical (pinned) version
- Version history is stored in `CoverLetterVersion` table
- Version index auto-increments (1, 2, 3...)

## CoverLetterData Pydantic Model

Create in `src/features/cover_letter/types.py`:

```python
class CoverLetterData(BaseModel):
    name: str
    title: str
    email: str  # With basic email format validation
    phone: str
    date: date
    body_paragraphs: list[str]  # Min 1, Max 4 paragraphs
```

**Validation Rules:**
- Require at least 1 paragraph
- Maximum 4 paragraphs
- Basic email format validation
- Methods: `model_dump_json()` for database storage, `model_validate_json()` for loading

---

# Database Migration

## Migration Strategy
- Update the SQLModel class definition in `src/database.py`
- SQLModel will auto-migrate on next app start (suitable for development)
- Since there is currently no cover letter data in the database, dropping the `content` column is safe
- All other data in the database (User, Job, Resume, etc.) will be preserved

**⚠️ Important**: This approach only works because no cover letter data exists. Future migrations must preserve data. Document the schema change in migration notes for future reference.

---

# Templates Page Implementation

## Tab Structure

Use `st.segmented_control` (like `app/pages/job.py`) with two tabs: 'Resume' and 'Cover Letter'

**Session State:**
- Persist selection in `st.session_state["selected_template_tab"]`
- Each tab maintains independent session state:
    - **Resume**: `resume_tmpl_chat_messages`, `resume_tmpl_versions`, `resume_tmpl_selected_idx`, `resume_tmpl_filename_input`
    - **Cover Letter**: `cover_tmpl_chat_messages`, `cover_tmpl_versions`, `cover_tmpl_selected_idx`, `cover_tmpl_filename_input`
- This ensures no re-rendering of inactive tabs and clean separation between workflows
- Users can switch between Resume and Cover Letter tabs while preserving their in-progress work in both tabs

### Migration of Existing Session State Keys

Current Templates page uses generic keys that need renaming:
- `tmpl_chat_messages` → `resume_tmpl_chat_messages`
- `tmpl_versions` → `resume_tmpl_versions`
- `tmpl_selected_idx` → `resume_tmpl_selected_idx`
- `tmpl_filename_input` → `resume_tmpl_filename_input`

This maintains consistency across resume and cover letter template workflows.

## Layout (Both Resume and Cover Letter Tabs)

Two-column layout with 50/50 split using `st.columns([1, 1])`

**Left Column:**
- Subheader: "Template Chat" (or "Resume Template Chat" / "Cover Letter Template Chat")
- Chat history in fixed-height scrollable container: `st.container(height=460, border=True)`
- Chat input with file upload support: `st.chat_input(accept_file=True, file_type=["png", "jpg", "jpeg", "webp"])`

**Right Column:**
- Navigation row: Preview label | ◀ | ▶ | Filename input | Download button
- PDF preview using `streamlit_pdf_viewer` with `width="100%"`, `height="stretch"`, `zoom_level="auto"`

## Cover Letter Template Generation Workflow

Duplicate and adapt the resume template workflow for cover letter tab:

**Session State Management:**
- `cover_tmpl_chat_messages`: list of chat messages
- `cover_tmpl_versions`: list of generated template versions with {html, pdf_bytes, label}
- `cover_tmpl_selected_idx`: current selected version index
- `cover_tmpl_filename_input`: download filename

**Features:**
- Chat interface allows user to describe desired template style
- Version labeling: v1, v2, v3... (same pattern as resume templates)
- Navigation: ◀ ▶ buttons to move between versions
- Download: saves selected template HTML to user's filesystem with filename pattern: `"cover_letter_template_{label}.html"` (e.g., "cover_letter_template_v1.html")
- Uses `generate_cover_letter_template_html()` for LLM generation
- Renders preview using `DUMMY_COVER_LETTER_DATA`

---

# Job Detail Page - Cover Letter Tab

## Overview

Two-column layout with 50/50 split (matches resume tab). Pattern similar to resume tab but manually edited (no AI generation for content).

**Versioning Support**: Cover letters have version tracking like resumes:
- Each Save creates a new `CoverLetterVersion` record
- User can navigate between versions with ◀ ▶ controls
- Version dropdown shows all versions (v1, v2, v3...)
- Pin functionality to mark canonical version

## Session State Management

**Session State Keys:**
- `cover_letter_draft`: `CoverLetterData` instance for current edits
- `cover_letter_last_saved`: `CoverLetterData` baseline for dirty detection
- `cover_letter_dirty`: bool indicating unsaved changes
- `cover_letter_template`: str for selected template name
- `cover_letter_template_saved`: str for baseline template
- `cover_letter_selected_version_id`: int | None for version navigation
- `cover_letter_loaded_from_version_id`: int | None to track reload state

**Initial Load (No Existing Cover Letter):**
- Pre-populate name, email, phone from user profile (`user.full_name`, `user.email`, `user.phone`)
- Set title to `job.job_title`
- Set date to current date
- Leave body_paragraphs as empty list
- Set template to "cover_000.html"

**Dirty State Tracking:**
- Compare current draft JSON to last saved JSON
- Save/Discard buttons enable/disable based on dirty state

**Version Selection Logic (Same as Resume):**
- Default to canonical version if exists, else head (latest) version
- Reload draft from selected version when version changes
- Keep working draft when dirty for same version

## Read-Only Mode (When Job Applied)

When `job.applied_at` is set:
- Cover letter becomes locked (same as resume)
- Disable all input fields
- Hide Save/Discard buttons
- Show only the saved canonical cover letter in preview
- Display info message: "Cover letter is locked because job status is Applied"

## Left Column Layout

**Subheader:** "Cover Letter Content"

**Version Navigation Controls** (when not read-only and versions exist):
- Horizontal container with right alignment
- ◀ button (disabled when at oldest version)
- Version dropdown (descending order: v3, v2, v1) with pin icon next to canonical version
- ▶ button (disabled when at newest version)
- Pin button (`:material/keep:` when canonical, `:material/keep_off:` otherwise)
- Same pattern as resume tab version controls

**Text Input Fields** (pre-populated from job/user profile on first load):
- **Name**: from user profile (`user.full_name`)
- **Title**: defaults to `job.job_title`
- **Email**: from user profile (`user.email`)
- **Phone**: from user profile (`user.phone`)
- **Date Picker**: defaults to current date
- All fields disabled when `job.applied_at` is set

**Body Paragraphs** (Single Text Area):
- Height: 350px
- User enters all paragraphs with blank lines between them
- On save, split on `\n\n` (double newlines) to create list of paragraphs
- Placeholder: "Enter your cover letter paragraphs here. Separate paragraphs with a blank line."
- Disabled when applied
- Implementation: Use `st.text_area()` with value as `"\n\n".join(body_paragraphs)`, then split by double newlines on save

**Template Selector Dropdown:**
- Lists available templates from `src/features/cover_letter/templates/`
- Same pattern as resume template selector
- Disabled when applied

**Button Row** (hidden when applied):
- **Save Button**: Creates new version in database
    - Disabled when not dirty or missing required fields (name, email)
- **Discard Button**: Reverts to last saved state
    - Disabled when not dirty

## Right Column Layout

**Subheader:** "Preview"

**Download Button** (right-aligned):
- Enabled only when cover letter is saved and not dirty
- Filename pattern: `"CoverLetter - {company} - {title} - {name} - {yyyy_mm_dd}.pdf"`

**PDF Preview:**
- Uses `streamlit_pdf_viewer` with `height="stretch"`
- Live preview updates as user edits fields
- Renders using `CoverLetterService.render_preview()`
- Disabled (show message) if missing required fields (name, email) or no templates available

---

# Cover Letter Feature Module

## Module Structure

Create new directory structure: `src/features/cover_letter/`

**Files:**
- `__init__.py`: Package initialization
- `types.py`: Pydantic models (`CoverLetterData`)
- `content.py`: Dummy data (`DUMMY_COVER_LETTER_DATA`)
- `llm_template.py`: LLM template generation (`generate_cover_letter_template_html`)
- `utils.py`: Utility functions (template listing, HTML/PDF conversion)
- `validation.py`: Template validation logic
- `templates/`: Directory for cover letter HTML templates

## Cover Letter Template Storage

**Directory:** `src/features/cover_letter/templates/`

**Templates:**
- Store cover letter HTML templates: `cover_000.html`, `cover_001.html`, etc.
- Templates use Jinja2 syntax with variables: `{{ name }}`, `{{ title }}`, `{{ email }}`, `{{ phone }}`, `{{ date }}`, `{% for paragraph in body_paragraphs %}`
- Cover letters should be single-page format

## Default Cover Letter Template (`cover_000.html`)

Create a professional default template as part of this sprint.

**Requirements:**
- Simple, clean design with standard business letter format
- Sender info top-left (name, email, phone)
- Date
- Salutation ("Dear Hiring Manager,")
- Body paragraphs with proper spacing (loop through `body_paragraphs`)
- Closing ("Sincerely,") with name
- Professional fonts (Arial or Calibri)
- Appropriate margins for business letters (~1 inch)
- Single-page constraint

**Path:** `src/features/cover_letter/templates/cover_000.html`

## Cover Letter Dummy Data (`content.py`)

Create `DUMMY_COVER_LETTER_DATA` in `src/features/cover_letter/content.py`

**Single Dummy Profile:**
- `name`: "Jane Smith"
- `title`: "Senior Software Engineer"
- `email`: "jane.smith@example.com"
- `phone`: "(555) 123-4567"
- `date`: current date
- `body_paragraphs`: List of 3 placeholder paragraphs:
    1. Opening expressing interest in position and company
    2. Middle paragraph highlighting relevant skills and experience
    3. Closing paragraph with call to action

Used for template preview rendering on Templates page.

## Template Validation (`validation.py`)

Create validation function similar to resume template validation.

**Required Jinja2 Variables:**
- `{{ name }}`
- `{{ email }}`
- `{{ date }}`
- At least one use of `body_paragraphs` (e.g., `{% for paragraph in body_paragraphs %}`)

**Optional Variables** (no warnings if missing):
- `{{ phone }}`
- `{{ title }}`

**Return Type:** `(is_valid: bool, warnings: list[str])`

## LLM Template Generation (`llm_template.py`)

**Function:** `generate_cover_letter_template_html(user_text: str, current_html: str | None, image: bytes | None) -> str`

**LLM Prompt Emphasis:**
- Single-page layout (business letter format)
- Professional letter format with clear hierarchy
- Proper spacing for recipient/sender info
- Readable body paragraph spacing
- Appropriate margins for business letters (~1 inch)
- Professional fonts
- Jinja2 template variables: `{{ name }}`, `{{ title }}`, `{{ email }}`, `{{ phone }}`, `{{ date }}`, `{% for paragraph in body_paragraphs %}`

**Implementation:**
- Similar structure to `src/features/resume/llm_template.py` but tailored for cover letters
- Same LLM model/configuration as resume templates
- Returns raw HTML (no markdown fences)

## Utils Module (`utils.py`)

Create utility functions mirroring resume utils structure:

**Functions:**
- `list_available_templates(templates_dir: Path) -> list[str]`: List HTML templates in directory, sorted alphabetically
- `convert_html_to_pdf(html: str, output_path: Path) -> None`: Convert rendered HTML to PDF using WeasyPrint
- `render_template_to_html(template_name: str, context: dict[str, Any], templates_dir: Path) -> str`: Render Jinja2 template with context

**Shared Functions:**
- Reuse `get_template_environment()` from `src/features/resume/utils.py` (not duplicated)

Follow same patterns as resume utils for consistency.

---

# Services

## CoverLetterTemplateService

**File:** `app/services/cover_letter_template_service.py`

Separate from `TemplateService` to keep resume and cover letter concerns organized.

**Methods:**
- `generate_version(user_text: str, image_file: bytes | None, current_html: str | None) -> TemplateVersion`: Generate cover letter template via LLM

**Implementation Details:**
- Returns `TemplateVersion` (same model as `TemplateService`, imported from `app/services/template_service`)
- Uses `DUMMY_COVER_LETTER_DATA` for preview rendering
- Validation via `src/features/cover_letter/validation.py`
- Same LLM model/configuration as resume templates

## CoverLetterService

**File:** `app/services/cover_letter_service.py`

**Versioning Methods:**
- `save_cover_letter(job_id: int, cover_data: CoverLetterData, template_name: str) -> DbCoverLetterVersion`: Save new version and update canonical
- `list_versions(job_id: int) -> list[DbCoverLetterVersion]`: Get all versions for a job, ordered by version_index
- `get_canonical(job_id: int) -> DbCoverLetter | None`: Retrieve canonical (pinned) cover letter
- `pin_canonical(job_id: int, version_id: int) -> None`: Set a version as canonical by copying to CoverLetter table

**Data Retrieval:**
- `get_cover_letter_for_job(job_id: int) -> DbCoverLetter | None`: Retrieve canonical cover letter for a job

**Rendering:**
- `render_preview(job_id: int, cover_data: CoverLetterData, template_name: str) -> bytes`: Render cover letter to PDF bytes for preview
- Uses session state caching similar to `ResumeService` (key: `cover_letter_pdf_cache`)

**Utilities:**
- `list_available_templates() -> list[str]`: List cover letter templates from `src/features/cover_letter/templates/`

**Implementation Patterns (Follow `ResumeService`):**
- Use database session management from `db_manager`
- Cache PDF previews in session state
- Include proper error handling and logging
- Update `Job.has_cover_letter` flag when saving
- Version index auto-increments (v1, v2, v3...)

---

# File Naming and Downloads

## Cover Letter Downloads

**Filename Pattern:** `"CoverLetter - {company} - {title} - {name} - {yyyy_mm_dd}.pdf"`

**Function Location:** `app/shared/filenames.py`

**Function Signature:** `build_cover_letter_download_filename(company_name: str, job_title: str, full_name: str) -> str`

## Template Downloads

**Filename Pattern:** `"cover_letter_template_{label}.html"` (e.g., "cover_letter_template_v1.html")

---

# Error Handling and Edge Cases

## Missing User Profile Data

On job cover letter tab, when pre-populating fields from user profile:
- If `user.full_name` is missing: leave name field empty
- If `user.email` is missing: leave email field empty
- If `user.phone` is missing: leave phone field empty

**Behavior:**
- Disable Save button until required fields (name, email) are filled
- Show warning message: "Required fields (name, email) must be filled before saving"

## Missing Cover Letter Templates

If no cover letter templates exist in `src/features/cover_letter/templates/`:
- Disable the PDF preview on job cover letter tab
- Show message: "No cover letter templates available. Create templates on the Templates page."
- Template dropdown should show error state

**⚠️ Important**: There should always be at least one template (`cover_000.html`) created as part of this sprint.

## Locked Cover Letters

When `job.applied_at` is set:
- Cover letter becomes read-only (locked)
- All input fields disabled
- Save/Discard buttons hidden
- Only saved cover letter shown in preview
- Same behavior as locked resumes

## Template Rendering Failures

**On Job Cover Letter Tab:**
- If PDF rendering fails:
    - Show error message: "Failed to render PDF preview"
    - Log exception with stack trace
    - Allow user to continue editing

**On Templates Page:**
- If template validation fails during generation:
    - Show warnings from validation
    - Still allow user to download/use template
    - Log validation failures

---

# Files to Create/Modify

## Files to Create

**Feature Module:**
- `src/features/cover_letter/__init__.py`: Package initialization
- `src/features/cover_letter/types.py`: Pydantic models (`CoverLetterData`)
- `src/features/cover_letter/content.py`: Dummy data (`DUMMY_COVER_LETTER_DATA`)
- `src/features/cover_letter/llm_template.py`: LLM template generation (`generate_cover_letter_template_html`)
- `src/features/cover_letter/utils.py`: Utility functions (template listing, HTML/PDF conversion)
- `src/features/cover_letter/validation.py`: Template validation logic
- `src/features/cover_letter/templates/cover_000.html`: Default professional cover letter template

**Services:**
- `app/services/cover_letter_service.py`: Business logic for cover letters (versioning, rendering, data management)
- `app/services/cover_letter_template_service.py`: Template generation service for Templates page

**UI Components:**
- `app/pages/job_tabs/cover.py`: Replace placeholder with full implementation for job cover letter tab

## Files to Modify

**Database:**
- `src/database.py`: 
    - Update `CoverLetter` table (remove `content`, add `cover_letter_json`, `template_name`)
    - Add new `CoverLetterVersion` table

**UI Pages:**
- `app/pages/templates.py`: Add tab structure, rename session state keys to `resume_tmpl_*`, add cover letter tab
- `app/pages/job.py`: May need updates if cover letter tab integration requires changes (verify existing implementation)

**Utilities:**
- `app/shared/filenames.py`: Add `build_cover_letter_download_filename()` function

---

# Acceptance Criteria

## Templates Page
- [ ] Templates page has Resume and Cover Letter tabs using `st.segmented_control`
- [ ] Tab selection persists in session state
- [ ] Each tab maintains independent session state and doesn't re-render when switching
- [ ] Cover letter tab has chat interface with same layout as resume tab (50/50 split)
- [ ] User can describe cover letter template style in chat
- [ ] AI generates cover letter template HTML with proper Jinja2 variables
- [ ] Generated templates are validated for required variables
- [ ] User can navigate between template versions using ◀ ▶ buttons
- [ ] User can download selected template as HTML file
- [ ] PDF preview renders correctly using dummy data

## Cover Letter Templates
- [ ] Default `cover_000.html` template exists and renders correctly
- [ ] Template uses professional business letter format
- [ ] Template includes all required Jinja2 variables: `{{ name }}`, `{{ email }}`, `{{ date }}`, `{% for paragraph in body_paragraphs %}`
- [ ] Template is single-page format with appropriate margins (~1 inch)
- [ ] Multiple templates can coexist in `src/features/cover_letter/templates/`

## Job Detail Cover Letter Tab
- [ ] Cover letter tab has two-column layout (50/50 split)
- [ ] Left column has input fields for name, email, phone, title, date, body paragraphs
- [ ] Fields pre-populate from user profile and job data on first load
- [ ] Body paragraphs use single textarea that splits on double newlines (`\n\n`)
- [ ] Template selector dropdown lists available templates
- [ ] Right column shows live PDF preview that updates as user edits
- [ ] Save button creates new version in database
- [ ] Version navigation controls (◀ ▶ dropdown pin) work correctly
- [ ] Pin button sets canonical version
- [ ] Dirty state tracking works (Save/Discard buttons enable/disable correctly)
- [ ] Download button generates PDF with correct filename format
- [ ] Download only enabled when cover letter is saved and not dirty

## Versioning
- [ ] Each save creates new `CoverLetterVersion` record with auto-incrementing version_index
- [ ] User can navigate between versions
- [ ] Selected version loads into editor
- [ ] Canonical version is indicated with pin icon in version dropdown
- [ ] Version dropdown shows all versions in descending order (newest first)

## Read-Only Mode
- [ ] When `job.applied_at` is set, all input fields are disabled
- [ ] Save/Discard buttons are hidden when applied
- [ ] Only canonical cover letter is shown in preview
- [ ] Info message displayed: "Cover letter is locked because job status is Applied"

## Error Handling
- [ ] Missing user profile data (name/email) shows warning and disables Save
- [ ] Missing templates disables preview with appropriate message
- [ ] PDF rendering failures show error message and allow continued editing
- [ ] Template validation failures show warnings but allow download
- [ ] All errors are logged with stack traces

## Data Integrity
- [ ] `Job.has_cover_letter` flag updates when cover letter is saved
- [ ] Cover letter JSON stores all required fields correctly
- [ ] Database schema migration preserves all non-cover-letter data
- [ ] Version history maintains complete snapshots of cover letter data

---

# Dependencies and Assumptions

## Dependencies
- Existing Streamlit infrastructure and session state management
- Jinja2 for template rendering
- WeasyPrint for PDF generation
- LLM access (same model/configuration as resume template generation)
- Existing `TemplateService` and `ResumeService` patterns to follow
- `streamlit_pdf_viewer` component for PDF preview

## Assumptions
- User profile data (name, email) exists for pre-population (or can be filled manually)
- At least one cover letter template (`cover_000.html`) will always exist after sprint completion
- Database auto-migration via SQLModel is acceptable for development environment
- No cover letter data currently exists in production database (safe to drop `content` column)
- Session state migration from `tmpl_*` to `resume_tmpl_*` keys is acceptable

---

# Additional Notes

- The version dropdown for both resume and cover letter tabs should include a pin icon next to the version that is pinned (canonical)
- Cover letters support full versioning with manual saves (no AI generation for content, only for templates)
- Body paragraphs input splits on double newlines (`\n\n`) to create paragraph list
- Template generation uses same LLM model as resume templates for consistency
- This sprint focuses on manual cover letter content creation; AI-assisted cover letter generation may be added in a future sprint

