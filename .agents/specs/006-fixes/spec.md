## Sprint 006 – Profile, Resume, and Jobs UX/Data Fixes

### Overview
This sprint finalizes a set of UX cleanups and schema alignments across the Profile page, Job pages (Overview and Resume tabs), and shared UI elements. It standardizes date handling across the app, aligns education data between the database and resume generation, adds support for Certificates at the profile/database level, and introduces a consistent approach for action buttons and delete confirmations. It also introduces a centralized place for UI constants and consolidates a shared Status Badge component. Logging is simplified to a single file with rotation.

Key themes:
- Rename the Profile page module and update references.
- Standardize date inputs (min date only) app-wide via constants.
- Align Education schema with `ResumeData` and add Experience `location`.
- Introduce Certificates feature (DB + Profile UI).
- Clean up Profile experience UI using a card layout with icon-only actions.
- Enhance Job pages: Overview layout polish, in-place editing, consistent badges/buttons; Resume tab add-object dialogs with immediate draft updates and preview refresh.
- Logging: single rotating file, no historical backups.

---

### User Stories
- As a user, I can manage my profile (personal info, experience, education, certificates) from a clean, consistent page using icon-only Edit/Delete card actions and confirmation dialogs.
- As a user, I can set dates anywhere in the app starting from Jan 1, 1950, without arbitrary maxima.
- As a user, I can enter my education using institution/degree/major/grad date and see that reflected in resume generation.
- As a user, I can add Certificates to my profile and see them reflected where appropriate (not yet used in resume content beyond title/date).
- As a user, I can add new Experience/Education/Certificates to a resume draft via dialogs on the Job → Resume tab; submitting updates the draft immediately, marks it dirty, and re-renders the preview.
- As a user, I can quickly adjust job metadata from the Job → Overview tab with a clean layout, a shared Status Badge, a favorite toggle, and in-place editing for title, company, description, and status. The download button copy is consistent.

---

### Data Model Changes (src/database.py)
- Experience
  - Add field: `location: str | None = Field(default=None)`.
- Education (BREAKING CHANGE; recreate DB per note)
  - Replace fields with:
    - `institution: str`
    - `degree: str`
    - `major: str`
    - `grad_date: date`
- Certification (new model)
  - Fields:
    - `id: int | None = Field(default=None, primary_key=True)`
    - `user_id: int = Field(foreign_key="user.id")`
    - `title: str`
    - `institution: str | None = Field(default=None)`
    - `date: date`
    - `created_at: datetime = Field(default_factory=datetime.now)`
    - `updated_at: datetime = Field(default_factory=datetime.now)`

Notes:
- Migrations are not required this sprint; delete the SQLite DB file to reset schema. The app will recreate it.

Impacts and alignment:
- `src/features/resume/types.py` already uses `ResumeEducation` with `institution/degree/major/grad_date` and `ResumeExperience` with `location`; this sprint aligns DB models accordingly.

---

### Constants and Shared Components
- Add UI constants module for consistent date limits.
  - Add new file: `app/constants.py`
    - Expose `MIN_DATE = date(1950, 1, 1)` as the only enforced bound for date inputs across the UI.
- Add shared Status Badge component (used in Jobs pages and anywhere else needed).
  - Add new file: `app/components/status_badge.py`
    - Export function `render_status_badge(status: str) -> None` that renders a consistent badge with icon/color by status.
    - Migrate usages from scattered implementations (e.g., `app/pages/jobs.py` and Job Overview) to this component.
- Add shared Delete Confirmation component for consistent UX.
  - Add new file: `app/components/confirm_delete.py`
    - Export function `confirm_delete(entity_label: str, on_confirm: Callable[[], None], on_cancel: Callable[[], None]) -> None`
    - UI: Heading/Body, primary "Delete" button and secondary "Cancel" button with text labels (no icons). This is one of the rare cases where Delete uses text, not an icon.

---

### UI/UX Specifications

#### Profile Page
- File rename
  - Rename `app/pages/user.py` → `app/pages/profile.py`.
  - Keep nav label as "Profile". Update all references to point to `pages/profile.py`.
  - Update `app/main.py` page registration and any `st.switch_page` or `st.page_link` calls.
  - Update references in `app/pages/job_tabs/resume.py` that currently link to `pages/user.py`.

- Experience section (cards)
  - Replace the current list render with a card layout (each item in a `st.container(border=True)`).
  - Card header row:
    - Left: `Title` (job title) as bold.
    - Right: Icon-only `Edit` and `Delete` material icon buttons, right-aligned.
  - Subheader line (single formatted string):
    - "Company | Location | Mon YYYY - Mon YYYY"; if end date is null, show "Present".
  - Content: A collapsed-by-default expander titled "Details" that shows the description content.
  - Delete opens the shared confirmation dialog from `app/components/confirm_delete.py`.
  - Edit button opens the existing Edit Experience dialog.
  - Use icon-only for Edit/Delete on cards; dialogs and forms use text verbs (Save/Cancel/Delete).

- Experience dialogs
  - `app/dialog/experience_dialog.py`
    - Add `Location` input for both Add and Edit dialogs.
    - Increase description textarea `height` to `300`.
    - Apply date bounds from `app/constants.py` for `min_value=MIN_DATE`. Do not set `max_value`.

- Education section
  - Align to new DB schema: show and edit `institution`, `degree`, `major`, `grad_date`.
  - Rendering: card containers with borders similar to Experience; icon-only Edit/Delete.
  - `app/dialog/education_dialog.py`
    - Replace current fields with `Institution`, `Degree`, `Major`, `Graduation Date`.
    - Graduation date is a single date (no start/end range).
    - Apply `min_value=MIN_DATE`, remove `max_value`.

- Certificates section (new)
  - Below Education, add Certificates management:
    - Card list with icon-only Edit/Delete.
    - Fields: `title` (required), `institution` (optional), `date` (required).
    - Add/Edit dialogs use text verbs for action buttons (Save/Cancel/Delete in dialog).
  - Implement `CertificateService` (see Services below).

- Visual polish
  - Wrap distinct objects (experience, education, certificates) in bordered containers to increase visual separation.
  - Buttons in header sections should be concise and use icons appropriately per these rules.

#### Job Page – Resume Tab
- Add-object dialogs
  - Add three new dialogs to create objects for the resume draft only (not persisted to DB on submit):
    - `app/dialog/resume_add_experience_dialog.py`
      - Fields: Title | Company, Location, Start Date | End Date (End Date optional), Points (textarea: each non-empty newline becomes a separate point).
      - Layout:
        - Row 1: columns [2, 2] → Title (left), Company (right)
        - Row 2: columns [4] → Location (full width)
        - Row 3: columns [2, 2] → Start Date (left), End Date (right)
        - Row 4: columns [4] → Points (textarea, full width)
    - `app/dialog/resume_add_education_dialog.py`
      - Fields: Institution, Degree | Major, Grad Date.
      - Layout:
        - Row 1: columns [4] → Institution (full width)
        - Row 2: columns [2, 2] → Degree (left), Major (right)
        - Row 3: columns [2, 2] → Grad Date (left), (empty/right left unused)
    - `app/dialog/resume_add_certificate_dialog.py`
      - Fields: Title, Date.
      - Layout:
        - Row 1: columns [3, 1] → Title (left, wide), Date (right)
  - On Submit: append to the in-memory resume draft (`st.session_state["resume_draft"]`), set `resume_dirty=True`, and re-render the PDF preview.
  - These dialogs are for adding new objects only. Editing of existing resume objects remains inline as currently implemented.
  - Date inputs must use `min_value=MIN_DATE` and no `max_value`.

- Integrate dialogs into UI
  - In `app/pages/job_tabs/resume.py`, replace or augment current "Add ..." buttons to open the respective dialogs instead of inserting empty items directly.
  - Ensure that after dialog submission, the preview is refreshed and dirty state is updated.

- Date pickers and labels
  - Ensure all date pickers in Resume tab (Experience, Education, Certificates) do not use `max_value` and respect `MIN_DATE`.
  - No label copy changes except standardization.

- Download button copy
  - When present, the header download button label should be "Download" (already implemented in Resume tab). No changes required here beyond ensuring consistency.

#### Job Page – Overview Tab (`app/pages/job_tabs/overview.py`)
- Layout
  - Header row (single line):
    - Left: Favorite star icon (visual only) if the job is a favorite.
    - Middle: `Title | Status Badge`.
    - Right: Icon-only Edit button, right-aligned.
  - Second row: `Company Name | Date Created | Date Applied`.
  - Main content area: two-column layout [4, 1]
    - Left: Description (collapsible remains OK; remove any unnecessary textual noise).
    - Right: Quick Actions column (same order and content as current, including favorite toggle as the first control; the toggle persists to DB on-change).

- In-place editing
  - Clicking the Edit icon transitions Title, Company, Job Description into editable inputs; Status becomes a dropdown. The Edit icon is replaced with text buttons "Save" and "Discard".
  - Persist changes via `JobService.update_job_fields`, extended to accept and persist `job_description`.

- Badges and copy
  - Replace any ad-hoc status widgets with the shared `app/components/status_badge.py` component.
  - Rename "Download Resume PDF" to "Download Resume" wherever displayed on Overview.
  - Remove any "(disabled)" suffix in button labels. The disabled state alone is sufficient.

#### Jobs Index (`app/pages/jobs.py`)
- Replace inline badge rendering with `app/components/status_badge.py`.
- No layout changes required beyond badge refactor.

#### Onboarding (`app/pages/_onboarding.py`)
- Step 2 (Experience)
  - Add `Location` input.
  - Update date pickers to use `min_value=MIN_DATE` and remove `max_value`.

- Step 3 (Education)
  - Collect: `Institution`, `Degree`, `Major`, `Graduation Date`.
  - Update date pickers to use `min_value=MIN_DATE` and remove `max_value`.

---

### Services
- ExperienceService (`app/services/experience_service.py`)
  - Accept and persist optional `location` during create/update.
  - Existing validations remain; ensure date parsing unaffected.

- EducationService (`app/services/education_service.py`)
  - Update validation and persistence to the new fields: `institution`, `degree`, `major`, `grad_date`.
  - Remove assumptions about start/end date.

- CertificateService (new)
  - Add file: `app/services/certificate_service.py` with CRUD operations for the new `Certification` model.
  - Mirror error handling/validation patterns from `ExperienceService`/`EducationService`.

- JobService (`app/services/job_service.py`)
  - Extend `update_job_fields(...)` to accept and persist `job_description`.
  - No other behavioral changes.

- Resume data adapter (`src/features/resume/data_adapter.py`)
  - Ensure it maps DB → `ResumeData` correctly with new Education/Experience fields.
  - Education: map `institution/degree/major/grad_date`.
  - Experience: include `location` when transforming.

---

### Shared/date handling
- Add `app/constants.py`:
  - `from datetime import date`
  - `MIN_DATE = date(1950, 1, 1)`
- Replace all date picker usages across the app to use `min_value=MIN_DATE` and remove any `max_value`.
  - Files to update:
    - `app/dialog/experience_dialog.py` (Add/Edit)
    - `app/dialog/education_dialog.py` (Add/Edit)
    - `app/pages/_onboarding.py` (Step 2 & Step 3)
    - `app/pages/job_tabs/resume.py` (ensure any date inputs adhere; no `max_value` anywhere)

---

### Logging
- Update `src/logging_config.py` to a single static file with rotation and no historical backups.
  - File sink: `log/resume-bot.log`
  - `rotation="20 MB"`
  - `retention=1` (keep only the current active file and the most recent rotated file).
  - Remove time from filename.

Note: If truly only one single file should exist at all times, set `retention=0` or an equivalent to prevent accumulation; however, Loguru typically keeps at least the rotated file. The intent for this sprint is to prevent growing historical logs; using `retention=1` is acceptable.

---

### Navigation and References
- Update `app/main.py` navigation to use `st.Page("pages/profile.py", title="Profile", icon=":material/person:")`.
- Update any `st.switch_page`/`st.page_link` calls that reference `pages/user.py` to `pages/profile.py`.
  - Specifically: `app/pages/job_tabs/resume.py` top-info banner button should target `"pages/profile.py"`.

---

### Files to Add / Edit / Rename
- Add
  - `app/constants.py`
  - `app/components/status_badge.py`
  - `app/components/confirm_delete.py`
  - `app/services/certificate_service.py`
  - `app/dialog/resume_add_experience_dialog.py`
  - `app/dialog/resume_add_education_dialog.py`
  - `app/dialog/resume_add_certificate_dialog.py`

- Rename
  - `app/pages/user.py` → `app/pages/profile.py` (update imports/references)

- Edit (non-exhaustive list; ensure coverage of every point above)
  - `src/database.py` (models: Experience+location, Education fields, new Certification)
  - `src/logging_config.py` (single rotating file)
  - `app/main.py` (page path)
  - `app/pages/job_tabs/resume.py` (dialogs integration, date constants, add buttons behavior)
  - `app/pages/job_tabs/overview.py` (layout, in-place editing, badge component, labels)
  - `app/pages/jobs.py` (badge component)
  - `app/pages/_onboarding.py` (location, education fields, min date only)
  - `app/dialog/experience_dialog.py` (location, textarea height 300, min date only)
  - `app/dialog/education_dialog.py` (new fields, min date only)
  - `app/pages/profile.py` (migrated from user.py; implement card layout, certificates section, delete confirmation)
  - `app/services/experience_service.py` (location)
  - `app/services/education_service.py` (new fields)
  - `app/services/job_service.py` (update_job_fields to include job_description)
  - `src/features/resume/data_adapter.py` (mapping updates)

---

### Behavior Details and Formats
- Date formats
  - UI: Render dates as `Mon YYYY` in profile cards. If end date missing, render `Present`.
  - Resume JSON: Continue using ISO-like `YYYY-MM-DD` strings as currently done by the Resume tab.

- Points parsing (Resume tab add experience dialog)
  - Split textarea by newline. Each non-empty line trims whitespace and becomes a separate bullet point.

- Delete confirmation
  - Uses shared component, primary "Delete", secondary "Cancel" (text only).

- Buttons and icons
  - Cards: icon-only for Edit/Delete.
  - Dialogs/forms: verb text (Save/Cancel/Delete), no icons on the primary actions unless explicitly documented otherwise.

---

### Acceptance Criteria
1) Profile page
- The page file is `app/pages/profile.py` and nav shows "Profile".
- Experience items render as bordered cards with: title header, right-aligned icon-only Edit/Delete; subheader line with "Company | Location | Mon YYYY - Mon YYYY"; expander labeled "Details" showing description.
- Experience Add/Edit dialogs include `Location` and description height is 300. Date pickers use `MIN_DATE` and no `max_value`.
- Education Add/Edit dialogs and list use `institution/degree/major/grad_date`.
- Certificates section exists below Education with add/edit/delete and card layout.

2) Resume tab
- Clicking Add Experience/Education/Certificate opens a dialog; on submit, the draft updates immediately, dirty state is true, and preview refreshes.
- Date pickers in dialogs use `MIN_DATE` and do not set `max_value`.

3) Jobs Overview
- Header shows: optional star icon, Title | Status Badge, right-aligned Edit icon.
- Second row shows: Company | Created | Applied.
- Description and Quick Actions render in two columns [4, 1].
- Edit toggles in-place editing (Title, Company, Description, Status) and provides Save/Discard.
- "Download Resume PDF" labels are changed to "Download Resume"; no "(disabled)" suffix on any button label.

4) Shared components and constants
- `app/components/status_badge.py` is used in Jobs pages.
- `app/components/confirm_delete.py` is used where delete confirmations appear on Profile items.
- `app/constants.py` is imported wherever date pickers are present; all date pickers respect `MIN_DATE` and remove any `max_value`.

5) Services and DB
- `Experience.location` is persisted where provided; `Education` schema matches `ResumeData` and `Certification` model exists.
- `JobService.update_job_fields` persists `job_description`.
- `src/features/resume/data_adapter.py` maps DB fields to `ResumeData` fields correctly.

6) Logging
- Only a single log file target `log/resume-bot.log` is configured with 20MB rotation and no multi-file historical backups beyond the immediately rotated one.

---

### Rationale and Notes
- Education alignment resolves mismatches between DB and `ResumeData`, enabling accurate PDF rendering and LLM transformations.
- Using a single `MIN_DATE` constant eliminates duplicated magic numbers and simplifies future adjustments.
- Icon vs text conventions improve clarity and consistency: icons for inline card actions; text for dialog/form verbs.
- Centralized Status Badge prevents visual drift across tabs and pages.
- Add-object dialogs on the Resume tab provide a faster, cleaner data entry flow and ensure immediate preview feedback without forcing DB persistence.
- Logging switch reduces file sprawl while keeping logs useful for development.

---

### Implementation Tips
- After schema changes, delete the existing SQLite DB file (per Notes) so the app can recreate tables.
- Use `from app.constants import MIN_DATE` in all UI modules with date inputs.
- For date formatting in Profile cards, prefer `dt.strftime("%b %Y")`.
- Keep existing error handling/logging patterns from current services; use `logger.exception` in except blocks for stack traces where appropriate.
- Ensure all page links (`st.switch_page`, `st.page_link`, banners) target `pages/profile.py`.
