# Spec Tasks

## Tasks

- [ ] 1. Backend API Endpoints - Add Missing Endpoints
  - [ ] 1.1 Create `DELETE /api/v1/jobs/bulk-delete` endpoint in `/apps/api/api/routes/jobs.py`
  - [ ] 1.2 Implement `bulk_delete_jobs` method in `/apps/api/api/services/job_service.py`
  - [ ] 1.3 Add or fix `GET /api/v1/jobs/{job_id}/resumes/current` endpoint in `/apps/api/api/routes/resumes.py`
  - [ ] 1.4 Add or fix `GET /api/v1/jobs/{job_id}/cover-letters/current` endpoint in `/apps/api/api/routes/cover_letters.py`
  - [ ] 1.5 Verify/create `POST /api/v1/workflows/extract-job-details` endpoint in `/apps/api/api/routes/workflows.py`
  - [ ] 1.6 Test all new/updated endpoints

- [ ] 2. Backend API Endpoints - Pagination & Stats
  - [ ] 2.1 Add `skip` and `limit` query parameters to `GET /api/v1/jobs` endpoint in `/apps/api/api/routes/jobs.py`
  - [ ] 2.2 Update `list_jobs` method in `/apps/api/api/services/job_service.py` to support pagination
  - [ ] 2.3 Return total count in jobs list response for pagination UI
  - [ ] 2.4 Create `GET /api/v1/users/{user_id}/stats` endpoint for dashboard statistics
  - [ ] 2.5 Implement stats computation (7-day, 30-day, total applications, etc.)

- [ ] 3. Profile Page - User Information & Empty Fields
  - [ ] 3.1 Add "Edit Profile" button to Profile Information section header in `/apps/web/src/app/profile/page.tsx`
  - [ ] 3.2 Create edit profile dialog component with form for user fields (first_name, last_name, email, phone, city, state, linkedin_url, github_url)
  - [ ] 3.3 Add validation for email format and URL formats
  - [ ] 3.4 Update profile display to show all fields with "Not provided" placeholder text for empty values
  - [ ] 3.5 Display success/error toasts on save
  - [ ] 3.6 Test PATCH `/api/v1/users/{user_id}` endpoint integration

- [ ] 4. Profile Page - Section Structure & Delete Confirmations
  - [ ] 4.1 Remove outer Card components wrapping sections in `/apps/web/src/app/profile/page.tsx`
  - [ ] 4.2 Replace with styled h2 section headers for Profile Information, Work Experience, Education, Certificates
  - [ ] 4.3 Move "Add" buttons to section header rows (right-aligned)
  - [ ] 4.4 Create reusable delete confirmation dialog component
  - [ ] 4.5 Add confirmation dialogs to Experience, Education, Certificate, and Achievement deletions
  - [ ] 4.6 Ensure dialog shows item name/title and destructive styling

- [ ] 5. Profile Page - Experience Cards Display
  - [ ] 5.1 Add company_overview field to ExperienceCard in `/apps/web/src/components/profile/ExperienceCard.tsx`
  - [ ] 5.2 Implement 300-character truncation with "show more"/"show less" toggle for company_overview
  - [ ] 5.3 Apply same truncation pattern to role_overview field
  - [ ] 5.4 Increase Edit Experience dialog width from `max-w-2xl` to `max-w-3xl` in ExperienceCard
  - [ ] 5.5 Increase Add Experience dialog width in `/apps/web/src/app/profile/page.tsx`
  - [ ] 5.6 Test truncation behavior with long and short text

- [ ] 6. Profile Page - Achievement Display & Dialog
  - [ ] 6.1 Remove borders around individual achievements in `/apps/web/src/components/profile/ExperienceCard.tsx`
  - [ ] 6.2 Add spacing between achievements for visual separation
  - [ ] 6.3 Change "Add Achievement" button from icon-only to button with Plus icon and text
  - [ ] 6.4 Add achievement count indicator to section header ("Achievements (3)")
  - [ ] 6.5 Increase achievement dialog to `max-w-2xl` and add `max-h-[80vh]`
  - [ ] 6.6 Increase Textarea rows for achievement content from 4 to 25

- [ ] 7. Jobs Page - Table Layout & Filters
  - [ ] 7.1 Replace JobCard grid with shadcn/ui Table component in `/apps/web/src/app/jobs/page.tsx`
  - [ ] 7.2 Add table columns: Checkbox, Job Title, Company, Favorite, Status, Date Added, Resume/Cover Letter badges, Actions
  - [ ] 7.3 Implement row hover states and clickable rows (navigate to job detail)
  - [ ] 7.4 Make columns sortable (default: created_at desc)
  - [ ] 7.5 Redesign filters to single-row horizontal layout (~40-50px height)
  - [ ] 7.6 Implement multi-select status filter with checkboxes
  - [ ] 7.7 Replace "Favorites" button with "Show favorites only" checkbox
  - [ ] 7.8 Update "Add Job" button to navigate to `/intake/new`

- [ ] 8. Jobs Page - Bulk Delete & Pagination
  - [ ] 8.1 Add checkbox column as first column in table
  - [ ] 8.2 Add "Select All" checkbox in table header
  - [ ] 8.3 Show bulk actions toolbar when ≥1 job selected (display count)
  - [ ] 8.4 Implement "Delete Selected" button with confirmation dialog
  - [ ] 8.5 Integrate with bulk delete API endpoint
  - [ ] 8.6 Implement server-side pagination (50 jobs per page)
  - [ ] 8.7 Add pagination controls (page numbers, prev/next, total count display)
  - [ ] 8.8 Track current page in URL query params

- [ ] 9. Job Detail - Overview Tab Actions Menu
  - [ ] 9.1 Add DropdownMenu component with MoreVertical icon to `/apps/web/src/components/job-detail/OverviewTab.tsx`
  - [ ] 9.2 Position menu on same row as edit/delete buttons, far right
  - [ ] 9.3 Add "Download Resume" action (enabled if canonical resume exists)
  - [ ] 9.4 Add "Download Cover Letter" action (disabled placeholder)
  - [ ] 9.5 Add "Copy Cover Letter" action (disabled placeholder)
  - [ ] 9.6 Implement "Copy Job Context" action with XML-formatted output
  - [ ] 9.7 Fetch work experience, job description, gap analysis, stakeholder analysis for copy action
  - [ ] 9.8 Display success toast on copy actions

- [ ] 10. Job Detail - Resume Tab Layout & Version Navigation
  - [ ] 10.1 Create two-column layout in `/apps/web/src/components/job-detail/ResumeTab.tsx` (60/40 split)
  - [ ] 10.2 Add instructions/prompt textarea (300px height) in left column
  - [ ] 10.3 Add control row with template selector, Generate, Save, Discard buttons
  - [ ] 10.4 Implement version navigation bar (ChevronLeft, dropdown, ChevronRight, Pin button)
  - [ ] 10.5 Show version dropdown with "v{N}" and "(pinned)" indicator
  - [ ] 10.6 Implement pin/unpin version functionality
  - [ ] 10.7 Add unsaved changes prompt when navigating between versions
  - [ ] 10.8 Hide version controls when job status is "Applied" (read-only mode)

- [ ] 11. Job Detail - Resume Tab Content & Preview
  - [ ] 11.1 Create Tabs component for resume sections (Profile, Experience, Education, Certifications, Skills)
  - [ ] 11.2 Implement Profile tab with name, title, email, phone, LinkedIn, summary fields
  - [ ] 11.3 Implement Experience tab with bordered containers, points textarea (350px), delete buttons
  - [ ] 11.4 Implement Education and Certifications tabs with add/delete functionality
  - [ ] 11.5 Implement Skills tab with textarea (400px) and comma/newline formatting
  - [ ] 11.6 Add right column with "Preview" header, Copy, and Download buttons
  - [ ] 11.7 Integrate PDF preview component (update only on save/generate)
  - [ ] 11.8 Implement dirty state tracking and enable/disable buttons accordingly

- [ ] 12. Job Detail - Resume Tab Validation & API Integration
  - [ ] 12.1 Add validation requiring name and email before Generate/preview
  - [ ] 12.2 Check for at least one profile experience before enabling Generate
  - [ ] 12.3 Show clear error messages for missing requirements
  - [ ] 12.4 Integrate with `GET /api/v1/jobs/{job_id}/resumes/versions` endpoint
  - [ ] 12.5 Integrate with `POST /api/v1/jobs/{job_id}/resumes/versions` for saving
  - [ ] 12.6 Integrate with `POST /api/v1/jobs/{job_id}/resumes/pin` for pinning
  - [ ] 12.7 Integrate with `POST /api/v1/workflows/resume-generation` for AI generation
  - [ ] 12.8 Create API client methods in `/apps/web/src/lib/api/resumes.ts` if needed

- [ ] 13. Job Detail - Notes Tab Two-Column Layout
  - [ ] 13.1 Create two-column layout in `/apps/web/src/components/job-detail/NotesTab.tsx` (2/3 left, 1/3 right)
  - [ ] 13.2 Implement left column notes list (newest first, full content, no pagination)
  - [ ] 13.3 Add Edit and Delete buttons to each note card
  - [ ] 13.4 Implement inline edit mode for notes with Save/Discard buttons
  - [ ] 13.5 Add delete confirmation dialog with note preview
  - [ ] 13.6 Implement right column with large textarea for new notes
  - [ ] 13.7 Add Save and Discard buttons at bottom of right column
  - [ ] 13.8 Integrate with notes API endpoints (GET, POST, PATCH, DELETE)

- [ ] 14. Home Page - Dashboard Statistics
  - [ ] 14.1 Remove current job description form from `/apps/web/src/app/page.tsx`
  - [ ] 14.2 Add prominent "Add Job" button at top (navigates to `/intake/new`)
  - [ ] 14.3 Create grid/flex layout for stat cards
  - [ ] 14.4 Add "Jobs Applied (Last 7 Days)" stat card
  - [ ] 14.5 Add "Jobs Applied (Last 30 Days)" stat card
  - [ ] 14.6 Add "Total Jobs Saved" and "Total Jobs Applied" stat cards
  - [ ] 14.7 Add optional metrics (Interviews, Offers, Favorites, Success rate)
  - [ ] 14.8 Integrate with stats API endpoint

- [ ] 15. Home Page - Activity Heat Map
  - [ ] 15.1 Install `react-calendar-heatmap` dependency
  - [ ] 15.2 Create `/apps/web/src/components/dashboard/ActivityHeatMap.tsx` component
  - [ ] 15.3 Configure 52-week grid (7 rows × 52 columns)
  - [ ] 15.4 Add Y-axis labels (Mon, Wed, Fri only)
  - [ ] 15.5 Add X-axis month labels above first day of each month
  - [ ] 15.6 Implement 5-level color scale (0, 1-2, 3-5, 6-9, 10+ applications)
  - [ ] 15.7 Add legend below chart (gradient from "Less" to "More")
  - [ ] 15.8 Implement tooltips showing date and application count on hover
  - [ ] 15.9 Query and format application data by date
  - [ ] 15.10 Add heat map component to home page

- [ ] 16. Job Intake - Single-Step Workflow
  - [ ] 16.1 Modify `/apps/web/src/app/intake/new/page.tsx` to be Step 1 (details form)
  - [ ] 16.2 Add large Job Description textarea (400px height)
  - [ ] 16.3 Add "Parse Info" button at top-right of form
  - [ ] 16.4 Add Job Title and Company text inputs
  - [ ] 16.5 Add Favorite checkbox
  - [ ] 16.6 Implement Parse Info button to call extraction workflow
  - [ ] 16.7 Populate title/company fields with extracted values
  - [ ] 16.8 Show loading state during extraction
  - [ ] 16.9 Handle extraction failures with warning message
  - [ ] 16.10 Enable Next button only when title and company have values
  - [ ] 16.11 Create job on Next click and navigate to Step 2
  - [ ] 16.12 Add navigation guard for leaving with unsaved data
  - [ ] 16.13 Update layout to remove Step 0 references
  - [ ] 16.14 Update home and jobs page buttons to link to `/intake/new`

