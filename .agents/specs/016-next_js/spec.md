# Profile Page

## User Profile Information Editing

Add an "Edit Profile" button that opens a dialog modal with a form for editing user profile fields (first_name, last_name, email, phone_number, city, state, linkedin_url, github_url). This dialog pattern is consistent with the existing edit pattern for experiences and other profile objects.

**API Endpoint:** `PATCH /api/v1/users/{user_id}` (endpoint already exists, verify functionality)

**Implementation:**

- Add "Edit Profile" button to the Profile Information section header
- Create a dialog component similar to the Edit Experience dialog
- Form should include all editable user fields
- Validate email format and URL formats (LinkedIn, GitHub)
- Display success/error toasts on save

## Display Empty Profile Fields

Display all user profile fields regardless of whether they have values. Empty fields should show placeholder text like "Not provided" or "Add [field name]" in a muted style. This makes it clear what information is missing and provides visual prompts to complete the profile.

**Fields to always display:**

- Name (first_name + last_name)
- Email
- Phone
- Location (city, state)
- LinkedIn URL
- GitHub URL

## Company Overview Field in Experience Cards

Add the `company_overview` field to the experience card display in the profile page. Display first 300 characters. If longer than 300 characters, append "... show more" as clickable text that expands to full content. When expanded, show full content with "show less" link to collapse back to 300 characters. Apply the same pattern to `role_overview` field.

**Location:** `/apps/web/src/components/profile/ExperienceCard.tsx`

## Edit Experience Dialog Width

Increase the Edit Experience dialog width from `max-w-2xl` to `max-w-3xl` to provide more horizontal space for form fields and improve readability.

**Files to update:**

- `/apps/web/src/components/profile/ExperienceCard.tsx` (Edit Experience dialog)
- `/apps/web/src/app/profile/page.tsx` (Add Experience dialog)

## Section Structure - Remove Nested Cards

Remove the outer `Card` components wrapping "Profile Information", "Work Experience", "Education", and "Certificates" sections. Replace with styled section headers (h2 elements with proper styling). Keep individual experience/education/certificate items as cards. The "Add" buttons move to the section header row.

**Layout Pattern:**

```
Section Header (h2 with styling)
├── Section Title
├── Add Button (aligned right)
└── Individual Item Cards
    ├── Item Card 1
    ├── Item Card 2
    └── Item Card 3
```

**Files to update:** `/apps/web/src/app/profile/page.tsx`

## Delete Confirmation Dialogs

Implement confirmation dialogs for all significant object deletions:

- Experiences
- Education entries
- Certificates
- Achievements
- Any other primary profile data

Each confirmation dialog should:

- Display the item name/title being deleted
- State "Are you sure you want to delete [item type]? This action cannot be undone."
- Have Cancel and Delete buttons
- Use destructive button styling (`variant="destructive"`)

## Achievement Dialog Size

Increase the achievement dialog size:

- Change `DialogContent` to `max-w-2xl`
- Add minimum height or use `max-h-[80vh]` for better vertical space
- Increase `Textarea` rows for content field from 4 to 25

**File to update:** `/apps/web/src/components/profile/ExperienceCard.tsx`

## Experience Card Achievement Display

Within each experience card, restructure the achievement display:

1. **Remove borders around individual achievements** but keep them visually separated with spacing
2. **Change Add Achievement button** from icon-only to a button with Plus icon and "Add Achievement" text, matching the style of "Add Experience"
3. **Add expansion indicator** - Show a count badge or "See more" text in the achievements section header ("Achievements (3)")

**File to update:** `/apps/web/src/components/profile/ExperienceCard.tsx`

# Jobs Page

## Convert to Table Layout

Replace the current grid of `JobCard` components with a table using the shadcn/ui `Table` component.

**Table Columns:**

- Checkbox (for multi-select bulk actions)
- Job Title (clickable link to job detail page)
- Company
- Favorite (icon/toggle for quick favoriting)
- Status (displayed as badge component)
- Date Added (created_at timestamp)
- Resume & Cover Letter badges (if they have one)
- Actions (dropdown menu with edit, delete, etc.)

**Table Features:**

- Row hover states for better UX
- Clickable rows that navigate to job detail page (entire row except action buttons)
- Sortable columns (initially sort by created_at desc)
- Responsive design for mobile/tablet

**File to update:** `/apps/web/src/app/jobs/page.tsx`

## Add Job Button

The "Add Job" button on the jobs page should navigate to the first step of the job intake workflow (Step 1 - job details with parse button). See the "Job Intake Workflow" section for complete workflow details.

**Navigation:** Link to `/intake/new`

## Compact Filters Layout

Redesign the filters section to be more compact and take up less vertical space. Use a single-row horizontal layout for all filter controls.

**Layout:**

- Arrange all filters in a single horizontal row with compact sizing
- Order: [Status multi-select dropdown] [Favorites checkbox] [Search input if exists]
- Target total height: ~40-50px
- Use compact button/dropdown sizes and minimal spacing between elements
- Ensure responsive behavior for smaller screens

## Multi-Select Status Filter

Replace the current single-select status dropdown with a multi-select component with checkboxes. Allow users to select multiple status values simultaneously. Update the filter logic to show jobs matching any of the selected statuses (OR logic).

**Implementation:**

- Use a multi-select dropdown component (or custom implementation with checkboxes)
- Allow selection of multiple statuses: Saved, Applied, Interviewing, Not Selected, No Offer, Hired
- Display selected filters as pills/badges for clarity
- "Clear all" option to reset filters

## Favorites Filter

Replace the current "Favorites" button with a checkbox labeled "Show favorites only" or "Favorites only". This provides a clearer boolean filter interface.

**File to update:** `/apps/web/src/app/jobs/page.tsx`

## Bulk Delete Functionality

Add checkbox selection to table rows for multi-select. When one or more jobs are selected, display a bulk actions toolbar with a "Delete Selected" button.

**Implementation:**

- Add checkbox column as first column in table
- Add "Select All" checkbox in table header
- Show bulk actions toolbar when ≥1 job selected
- Display count of selected jobs in toolbar
- "Delete Selected" button triggers confirmation dialog
- Confirmation dialog shows count and requires explicit confirmation
- Call bulk delete API endpoint

**Backend API Endpoint (NEW):**

Create `DELETE /api/v1/jobs/bulk-delete` endpoint that accepts:

```json
{
  "job_ids": [1, 2, 3, ...]
}
```

Endpoint should delete all specified jobs in a single transaction and return success/failure status for the operation.

**Files to update:**

- `/apps/web/src/app/jobs/page.tsx` (frontend table and bulk delete UI)
- `/apps/api/api/routes/jobs.py` (add bulk delete endpoint)
- `/apps/api/api/services/job_service.py` (add bulk delete method)

## Server-Side Pagination

Implement server-side pagination for scalability. Update the `/api/v1/jobs` endpoint to accept pagination parameters (offset/skip and limit).

**Pagination Settings:**

- 50 jobs per page
- Display page numbers, previous/next buttons
- Show total count and current range (e.g., "Showing 1-50 of 243")
- Optional: Jump to page input

**Backend Changes Required:**

- Add `skip` and `limit` query parameters to `/api/v1/jobs` endpoint
- Return total count in response for pagination UI
- Ensure queries are optimized with proper indexing

**Frontend Implementation:**

- Use pagination component (shadcn/ui (preferred) or custom (if necessary))
- Track current page in URL query params for bookmarking
- Handle loading states during page transitions

**Files to update:**

- `/apps/web/src/app/jobs/page.tsx`
- `/apps/api/api/routes/jobs.py` (add pagination parameters)
- `/apps/api/api/services/job_service.py` (implement pagination in list_jobs method)

# Job Page (Job Detail)

## Fix 404 Routes

The following endpoints are returning 404 errors:

- `GET /api/v1/jobs/{job_id}/resumes/current`
- `GET /api/v1/jobs/{job_id}/cover-letters/current`

**Resolution:** Add `/current` endpoints to the API.

**Implementation:**

Create the following endpoints:

- `GET /api/v1/jobs/{job_id}/resumes/current` - Returns the canonical/pinned resume for a job
- `GET /api/v1/jobs/{job_id}/cover-letters/current` - Returns the canonical/pinned cover letter for a job

Both endpoints should return:

- The canonical resource object if one exists
- Empty response (null or empty object) with 200 status if none exists
- Never return 404 when the job exists

This provides a clean, explicit API for accessing the "current" canonical version and simplifies frontend code.

**Files to update:**

- `/apps/api/api/routes/resumes.py` (add or fix /current endpoint)
- `/apps/api/api/routes/cover_letters.py` (add or fix /current endpoint)

## Job - Overview Tab

Add a dropdown actions menu to the overview tab. The actions menu icon (triple vertical dots/MoreVertical) should be positioned on the same row as any edit/delete buttons, aligned to the far right.

**Actions Menu Items:**

- **Download Resume** - Enabled if canonical resume exists; downloads the pinned resume PDF
- **Download Cover Letter** - Disabled placeholder for future functionality
- **Copy Cover Letter** - Disabled placeholder for future functionality
- **Copy Job Context** - Copies formatted job context to clipboard including:
  - Work experience (formatted with achievements)
  - Job description
  - Gap analysis (from intake session if exists)
  - Stakeholder analysis (from intake session if exists)

**Implementation:**

- Use shadcn/ui `DropdownMenu` component
- Icon: `MoreVertical` from lucide-react
- Position: Same row as existing action buttons, far right
- Conditional items: Download Resume enabled only if canonical resume exists
- Copy Job Context formats content in XML-style tags as in Streamlit app
- Display success toast on successful copy actions

**Reference:** See `/apps/api/app/pages/job_tabs/overview.py` and `/apps/api/app/components/copy_job_context_button.py` for Streamlit implementation details.

**File to update:** `/apps/web/src/components/job-detail/OverviewTab.tsx`

## Job - Resume Tab

Redesign the resume tab to match the Streamlit app structure and functionality with modern React/Next.js improvements. Based on analysis of `/apps/api/app/pages/job_tabs/resume.py`:

### Layout Structure

**Two-Column Layout:**

- **Left Column (wider, ~60%)**: Resume content editor and controls
- **Right Column (~40%)**: PDF preview and actions

### Left Column - Resume Content

**Top Section:**

1. **Instructions/Prompt Input** - Large textarea for "What should the AI change?" instructions (300px height)
2. **Control Row** with:
   - Template selector dropdown (right-aligned)
   - Generate button (primary, disabled if missing required fields or no experiences)
   - Save button (primary, disabled if not dirty or missing fields)
   - Discard button (disabled if not dirty)

**Version Navigation** (when versions exist and not read-only):

- Horizontal navigation bar with:
  - Left arrow (previous version) - use ChevronLeft icon from lucide-react
  - Version dropdown showing "v{N}" with "(pinned)" indicator for canonical
  - Right arrow (next version) - use ChevronRight icon from lucide-react
  - Pin/Unpin button - toggle between filled and outline pin icons
- Only visible when job is not Applied
- When navigating between versions with unsaved changes: prompt user with dialog asking to save, discard, or cancel navigation

**Resume Content Tabs:**

Use tabbed interface instead of collapsible expanders to give more focus to each section:

1. **Profile Tab** - Name, title, email, phone, LinkedIn, professional summary
2. **Experience Tab** - Each experience in bordered container with:
   - Title, company, location
   - Start/end dates
   - Points (textarea, one per line, 350px height, label indicates AI-editable)
   - Delete button for experience
   - Add Experience button at bottom
3. **Education Tab** - Institution, degree, major, graduation date, delete buttons
   - Add Education button at bottom
4. **Certifications Tab** - Title, date, delete buttons
   - Add Certification button at bottom
5. **Skills Tab** (AI-editable) - Textarea accepting commas/newlines (400px height)
   - Auto-formats to one skill per line

**Read-Only Mode:**

- When job status is "Applied", all fields are disabled/read-only
- Show canonical version only
- No save/generate/version controls

### Right Column - Preview

**Header Row:**

- "Preview" subheader
- Copy button - copies resume text to clipboard
- Download button (primary) - downloads canonical PDF
  - Only enabled for pinned version when not dirty and not read-only
  - Disabled states show helpful tooltips

**PDF Preview:**

- PDF preview using PDF viewer component
- Updates ONLY after save or generate actions (not real-time)
- Shows canonical version when read-only
- Warning if required fields missing

### Key Features

**Dirty State Tracking:**

- Compare current draft against last saved version
- Enable/disable Save and Discard buttons based on dirty state
- Show unsaved changes indicator
- When navigating between versions with unsaved changes, prompt user with save/discard/cancel dialog

**Version Management:**

- Create new version on Generate (event_type='generate')
- Create new version on Save (event_type='save')
- Pin version to set as canonical
- Prompt before navigating between versions if there are unsaved changes
- Versions ordered by version_index (v1, v2, v3...)

**Validation:**

- Require name and email before allowing Generate or showing preview
- Require at least one experience in profile
- Show clear error messages for missing requirements

**AI-Editable Fields** (indicated in UI labels):

- Title
- Professional Summary
- Experience points
- Skills

### API Integration

**Endpoints Used:**

- `GET /api/v1/jobs/{job_id}/resumes/versions` - List all versions
- `GET /api/v1/jobs/{job_id}/resumes/current` - Get canonical resume
- `POST /api/v1/jobs/{job_id}/resumes/versions` - Create new version
- `POST /api/v1/jobs/{job_id}/resumes/pin` - Pin version as canonical
- `POST /api/v1/workflows/resume-generation` - Generate resume with AI
- `POST /api/v1/jobs/{job_id}/resumes/preview` - Get preview PDF bytes

**Implementation Notes:**

- Use shadcn/ui Tabs component for resume content sections
- PDF preview should only refresh after explicit save or generate actions, not on every keystroke
- No reset functionality needed (not used in current Streamlit app)
- Version navigation should maintain consistency with Streamlit's arrow + dropdown + pin pattern

**Files to update:**

- `/apps/web/src/components/job-detail/ResumeTab.tsx` (complete rewrite)
- Create new API client methods in `/apps/web/src/lib/api/resumes.ts` if needed
- May need new backend endpoints to match Streamlit functionality

## Job - Notes Tab

Redesign the notes tab with a two-column layout for faster note-taking with fewer clicks.

### Two-Column Layout

**Left Column (2/3 width):**

- List of all notes (newest first)
- Each note displayed as a card with:
  - Note content (full text)
  - Timestamp
  - Edit and Delete action buttons
- No pagination (load all notes at once)
- Sufficient for current expected volume

**Inline Edit Mode:**

- Clicking Edit makes the note content editable in place
- Save and Discard buttons appear for that specific note
- Buttons respect dirty state of the individual note
- Save updates the note, Discard reverts changes

**Delete Confirmation:**

- Clicking Delete shows confirmation dialog
- Dialog displays note preview and requires explicit confirmation

**Right Column (1/3 width):**

- **Large textarea** for new note content (takes most of vertical space)
- **Save button** at bottom (primary, enabled when textarea has content/is dirty)
- **Discard button** at bottom (enabled when textarea is dirty)
- After saving, textarea clears and new note appears at top of list

### Implementation Details

**Note Display:**

- Newest notes first (sort by created_at desc)
- Each note card shows full content (no truncation)
- Adequate spacing between notes
- Clear visual distinction between view and edit modes

**State Management:**

- Track dirty state for add form separately from edit states
- Each note in edit mode has its own dirty state
- Only one note should be editable at a time (close others when opening new edit)

**API Endpoints:**

- `GET /api/v1/jobs/{job_id}/notes` - List all notes
- `POST /api/v1/jobs/{job_id}/notes` - Create note
- `PATCH /api/v1/jobs/{job_id}/notes/{note_id}` - Update note
- `DELETE /api/v1/jobs/{job_id}/notes/{note_id}` - Delete note

**Files to update:**

- `/apps/web/src/components/job-detail/NotesTab.tsx` (complete redesign)
- Create API client methods in `/apps/web/src/lib/api/notes.ts` if not exists

# Home Page

Redesign the home page as a dashboard-style layout providing a high-level overview of the user's job application activity. Remove the current job description textarea form and replace with summary statistics and a prominent "Add Job" action button.

## Layout and Components

### Add Job Button

Position prominently at the top of the page as the primary call-to-action. Clicking navigates to the job intake workflow (starting at Step 0 - paste job description).

**Button Styling:**

- Large, primary button
- Text: "Add Job"
- Icon: Plus icon from lucide-react
- Link to: `/intake/new` or similar intake starting route

### Dashboard Statistics

Display key metrics in a card-based dashboard layout.

**Required Metrics:**

1. **Jobs Applied (Last 7 Days)** - Count of jobs with status "Applied" where `applied_at` is within rolling 7-day window
2. **Jobs Applied (Last 30 Days)** - Count of jobs with status "Applied" where `applied_at` is within rolling 30-day window
3. **Total Jobs Saved** - Count of all jobs with status "Saved"
4. **Total Jobs Applied** - Count of all jobs with status "Applied" (all time)

**Additional Suggested Metrics:**

- Total interviews scheduled (jobs with status "Interviewing")
- Total offers received (jobs with status "Hired")
- Favorite jobs count
- Recent activity (last job added, last application)
- Success rate (offers / applications %)

**Dashboard Layout:**

- Grid or flex layout with stat cards
- Each card shows: metric label, large number, and optional subtitle/context
- Use consistent card styling (shadcn/ui Card component)
- Responsive design for mobile/tablet

### Application Activity Heat Map

Add a GitHub-style calendar heat map showing job application activity over the past 52 weeks. This provides a visual overview of application patterns over time.

**Layout Specifications:**

- **Time Range:** Previous 52 weeks (1 year)
- **Orientation:** Weekdays on y-axis, weeks on x-axis
- **Grid Structure:**
  - 52 columns (weeks), current week on far right, 52 weeks ago on far left
  - 7 rows (days), Sunday at top, Saturday at bottom
  - Each cell represents one day
- **Axis Labels:**
  - Y-axis: Show abbreviated weekday labels for Mon, Wed, Fri only (keeps layout clean)
  - X-axis (top): Show abbreviated month names (Jan, Feb, Mar, etc.) positioned above the column containing the first day of that month
- **Color Scale:**
  - 0 applications: background/neutral color
  - 1-2 applications: light green
  - 3-5 applications: medium green
  - 6-9 applications: darker green
  - 10+ applications: darkest green
- **Legend:** Display below chart showing gradient of 5 colors from "Less" to "More"
- **Tooltips:** On hover, display date and application count (e.g., "Nov 14, 2025: 3 applications")

**Implementation:**

- Use `react-calendar-heatmap` library (https://github.com/kevinsqi/react-calendar-heatmap)
- Data source: Query jobs by `applied_at` date, group by date, count per day
- Component should be responsive and scale appropriately

**Files to create:**

- `/apps/web/src/components/dashboard/ActivityHeatMap.tsx`

**Dependencies to add:**

- `react-calendar-heatmap`

## API Requirements

Add aggregation endpoint or compute stats on frontend from jobs list:

- `GET /api/v1/users/{user_id}/stats` - returns computed statistics

**Files to update:**

- `/apps/web/src/app/page.tsx` (complete redesign)
- Create or update API client methods in `/apps/web/src/lib/api/`
- Consider backend stats endpoint: `/apps/api/api/routes/stats.py` or add to users route

# Job Intake Workflow

Redesign the job intake workflow to improve user experience by consolidating the job description entry and information extraction into a single step.

## Current Problem

The current implementation crashes when trying to create a job because the frontend sends `title: null` and `company: null`, but the backend `save_job` service requires non-empty strings for these fields.

```
ValueError: title is required
```

## Solution: Single-Step with Parse Button

**Key Changes:**

1. Start directly at details step (no separate paste-only step)
2. Include job description textarea in the details form
3. Add "Parse Info" button to extract title and company from description
4. Do NOT create job record until form is submitted with valid title and company
5. User can manually enter or use Parse Info button to populate fields

## Workflow Steps

### Step 1: Job Details (Intake Start)

**Purpose:** Capture job description and details (title, company) in a single form before creating the job record.

**UI Layout:**

- Form with fields in this order:
  - **Job Description** - Large textarea (minimum 400px height) with placeholder: "Paste the full job description here..."
  - **Parse Info button** - Positioned at top-right of form, calls extraction workflow
  - **Job Title** - Text input (editable, can be manually entered or populated by Parse Info)
  - **Company** - Text input (editable, can be manually entered or populated by Parse Info)
  - **Favorite** - Checkbox, defaults to false
- Next button at bottom right (enabled when title and company have values)

**Behavior:**

- User pastes job description into textarea
- User can either:
  - Manually enter title and company, OR
  - Click "Parse Info" button to extract title and company from description
- Parse Info button:
  - Calls backend extraction workflow with job description
  - Populates Job Title and Company fields with extracted values
  - Can be clicked multiple times if user changes description
  - Shows loading state while extracting
- Click Next → **Create job record** with entered data
- Navigate to Step 2 (experience selection)

**Backend Call:**

- `POST /api/v1/jobs?user_id={id}` with complete job data including title, company, description
- Returns created job with job_id for subsequent steps

**Route:** `/intake/new` (starts directly at this step, no jobId yet)

### Step 2: Experience Selection (UNCHANGED)

Continue with existing Step 2 functionality for selecting experiences.

**Route:** `/intake/[jobId]/experience`

### Step 3: Proposal Review (UNCHANGED)

Continue with existing Step 3 functionality for reviewing proposals.

**Route:** `/intake/[jobId]/proposals`

## Workflow Navigation

**Entry Points:**

- Home page "Add Job" button → `/intake/new` (Step 1 - details form)
- Jobs page "Add Job" button → `/intake/new` (Step 1 - details form)

**Progression:**

1. Step 1 (enter/parse details) → Create job → Step 2 (select experiences)
2. Step 2 (select experiences) → Step 3 (review proposals)
3. Step 3 (complete) → Navigate to job detail page

**Back Navigation:**

- Standard back button behavior for Steps 2 and 3
- Step 2/3 use job_id in URL: `/intake/[jobId]/experience`, `/intake/[jobId]/proposals`

## State Management

**Workflow State (before job creation):**

- Hold job description, title, company in React form state
- No need for session storage since everything is in a single form
- Clear state after job creation when navigating to Step 2

**After Job Creation:**

- Use job_id from created job for Steps 2 and 3
- Store job_id in URL params: `/intake/[jobId]/experience`

## Backend Changes

### Job Extraction Workflow

**Endpoint:** May already exist, verify: `POST /api/v1/workflows/extract-job-details`

**Request Body:**

```json
{
  "job_description": "string"
}
```

**Response:**

```json
{
  "title": "extracted job title",
  "company": "extracted company name",
  "confidence": 0.95
}
```

**Implementation:**

- Use existing LLM workflow/agent for extraction
- Should extract: job title, company name
- Return with confidence score
- Handle extraction failures gracefully (allow manual entry)

### Job Creation

**Endpoint:** `POST /api/v1/jobs` (already exists)

**Update:** Ensure title and company are required, non-null fields. The schema already supports this - frontend just needs to provide values.

## Files to Update

**Frontend:**

- `/apps/web/src/app/intake/new/page.tsx` (MODIFY - becomes Step 1 with description + parse button)
- `/apps/web/src/app/intake/[jobId]/layout.tsx` (UPDATE - remove Step 0 from navigation)
- `/apps/web/src/lib/api/workflows.ts` (VERIFY/ADD - extraction workflow API client)

**Backend:**

- Verify extraction workflow exists: `/apps/api/api/routes/workflows.py`
- If needed, create extraction endpoint
- No changes needed to job creation endpoint (already validates correctly)

## Error Handling

**Extraction Failures:**

- If extraction fails or has low confidence, pre-fill form with empty values
- Show warning message: "Could not extract job details. Please enter manually."
- Allow user to proceed with manual entry

**Validation:**

- Step 1: Require non-empty title and company before allowing job creation
- Job description should have content but not strictly required
- Show inline validation errors for missing required fields

**Navigation Guards:**

- Prevent advancing from Step 1 without completing required fields (title, company)
- Show confirmation dialog if user tries to leave workflow with entered data but hasn't created the job
