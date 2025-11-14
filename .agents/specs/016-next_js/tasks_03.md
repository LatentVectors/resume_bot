# Spec Tasks

## Tasks

- [x] 1. Home Page Statistics Layout

  - [x] 1.1 Update home page to display primary stats row with three stats: "Jobs Applied (Last 7 Days)", "Jobs Applied (Last 30 Days)", "Days Since Last Application" - use text-3xl or larger for numbers
  - [x] 1.2 Add secondary stats row below primary with four smaller stats: "Total Jobs Applied", "Total Jobs Saved", "Interviews Scheduled", "Offers Received"
  - [x] 1.3 Remove card wrappers from statistics to reduce visual clutter
  - [x] 1.4 Implement "Days Since Last Application" calculation (days between today and most recent applied_at, format as "Today", "1 day", "X days", or "N/A")
  - [x] 1.5 Reduce gaps between statistics sections and heatmap for more compact layout

- [x] 2. Activity Heatmap Tooltips

  - [x] 2.1 Implement `titleForValue` function for react-calendar-heatmap to generate title attribute for each square
  - [x] 2.2 Implement `tooltipDataAttrs` function to set data attributes for tooltip generation
  - [x] 2.3 Format tooltip to display: formatted date and number of applications (e.g., "January 15, 2024 - 3 applications")
  - [x] 2.4 Test tooltip functionality across different date ranges and application counts

- [x] 3. Profile Page - Profile Information Card

  - [x] 3.1 Fix excessive gap above user's name by reducing padding/spacing in CardContent
  - [x] 3.2 Move edit button inside profile information card (currently outside)
  - [x] 3.3 Change edit button to icon-only (remove "Edit Profile" text), matching work experience edit button style
  - [x] 3.4 Position edit icon button in top-right corner of the card

- [x] 4. Profile Page - LinkedIn and GitHub Icons

  - [x] 4.1 Add lucide-react LinkedIn icon next to LinkedIn URL in profile information section
  - [x] 4.2 Add lucide-react GitHub icon next to GitHub URL in profile information section
  - [x] 4.3 Make icons clickable links that open URLs in new tab
  - [x] 4.4 Handle cases where URLs are missing (don't show icons)

- [x] 5. Profile Page - Achievements Section

  - [x] 5.1 Remove global expand/collapse button for achievements
  - [x] 5.2 Implement individual expand/collapse per achievement using accordion-style component
  - [x] 5.3 Set default state to collapsed (show only title)
  - [x] 5.4 Ensure expanded state shows title and full content
  - [x] 5.5 Verify achievements are visible even when collapsed

- [x] 6. Profile Page - Work Experience Card Improvements

  - [x] 6.1 Reduce gap between company name and date/location
  - [x] 6.2 Add "Company Overview" subheader before company overview content
  - [x] 6.3 Add "Role Overview" subheader before role overview content
  - [x] 6.4 Add "Skills" subheader before skills content
  - [x] 6.5 Display date and location on single line, separated by bullet or comma
  - [x] 6.6 Use smaller text size for date/location to reduce vertical space
  - [x] 6.7 Improve overall spacing to reduce visual clutter

- [x] 7. Jobs Page - Actions Button Fix

  - [x] 7.1 Add `onClick={(e) => e.stopPropagation()}` to actions button (MoreVertical icon) to prevent navigation
  - [x] 7.2 Verify dropdown/popover menu opens without navigating to job detail page
  - [x] 7.3 Test that actions button only triggers dropdown menu, not navigation

- [x] 8. Job Notes - Layout and Add Note Section

  - [x] 8.1 Implement two-column layout: 60% width for notes list (left), 40% width for add note form (right) using CSS Grid
  - [x] 8.2 Add vertical divider line between the two columns
  - [x] 8.3 Ensure responsive behavior (stack vertically on mobile)
  - [x] 8.4 Remove card wrapper around add note section (no card styling)
  - [x] 8.5 Remove "Add New Note" subheader
  - [x] 8.6 Change placeholder text from "write a note..." to "add new note here..."
  - [x] 8.7 Set fixed height textarea (fit on screen but not below 200px) with scrollable content
  - [x] 8.8 Rename buttons to "Save" and "Discard" (text only, no icons)
  - [x] 8.9 Position buttons above textarea input (not below)
  - [x] 8.10 Enable Save button only when there is content, Discard button always enabled

- [x] 9. Job Notes - Saved Notes Display and Edit Mode

  - [x] 9.1 Move date to top row, displayed as title on left side
  - [x] 9.2 Move edit and delete buttons to top-right corner
  - [x] 9.3 Change buttons to icon-only (no text labels)
  - [x] 9.4 Style delete icon as red or destructive action
  - [x] 9.5 Implement note content truncation after 500 characters with "..." indicator
  - [x] 9.6 Add "Show more" / "Show less" toggle to expand/collapse full content
  - [x] 9.7 In edit mode, replace edit/delete buttons with Discard and Save buttons at top
  - [x] 9.8 Enable Save button only when content has changed from original (dirty state)
  - [x] 9.9 Make Discard button always enabled, exits edit mode and discards changes

- [x] 10. Job Notes - Sticky Add Note Section

  - [x] 10.1 Implement CSS `position: sticky` for add note form
  - [x] 10.2 Set appropriate `top` offset to account for header/navigation
  - [x] 10.3 Ensure form doesn't overlap with fixed headers or navigation elements
  - [x] 10.4 Test scrolling behavior to confirm form stays visible at all scroll positions

- [x] 11. Job Intake Step 1 - Header and Field Layout

  - [x] 11.1 Update header text to "Job Intake: Step 1 of 3 - Job Details"
  - [x] 11.2 Remove subtitle "Step 1 of 3" (already in header)
  - [x] 11.3 Remove descriptive text "Enter the Job description and details..."
  - [x] 11.4 Restructure field layout: single row above job description with Favorite star icon (first), Job Title input (flex-1), Company Name input (flex-1)
  - [x] 11.5 Remove all field subtitles/descriptions
  - [x] 11.6 Add tooltips on hover: Job Title ("The title of the position you're applying for"), Company Name ("The name of the company offering this position"), Favorite ("Mark this job as favorite for easy access")

- [x] 12. Job Intake Step 1 - Parse Info Button and Next Button

  - [x] 12.1 Keep Parse Info button positioned in bottom-right corner above job description textarea
  - [x] 12.2 Add tooltip to Parse Info button: "Automatically extract job title and company name from the job description" using shadcn Tooltip component
  - [x] 12.3 Change Next button text from "Next: Select Experience" to "Next"
  - [x] 12.4 Verify Next button functionality and navigation behavior unchanged

- [x] 13. Job Intake Step 2 - Page Layout and Structure

  - [x] 13.1 Create full-height layout with header and action buttons at bottom
  - [x] 13.2 Implement header row: left side "Job Intake: Step 2 of 3 - Experience & Resume Development", right side copy job context button (tertiary style)
  - [x] 13.3 Create two-column grid layout: left 40% (chat), right 60% (tabs)
  - [x] 13.4 Set columns to fill available vertical space: `calc(100vh - header height - action buttons height)`
  - [x] 13.5 Add bottom action buttons row: Back button (left), Skip and Next buttons (right, Next disabled until version pinned)
  - [x] 13.6 Implement responsive behavior: stack columns vertically on mobile (< 768px)

- [x] 14. Job Intake Step 2 - Chat Interface UI

  - [x] 14.1 Install and configure shadcn-chatbot-kit components
  - [x] 14.2 Add "Resume Agent" title above message container
  - [x] 14.3 Create fixed-height scrollable container (550px) for message history
  - [x] 14.4 Add chat input at bottom with placeholder "Ask for resume changes..."
  - [x] 14.5 Style user messages as right-aligned with distinct styling
  - [x] 14.6 Style assistant messages as left-aligned with distinct styling
  - [x] 14.7 Style tool messages with subtle styling, shown as captions
  - [x] 14.8 Skip rendering assistant messages that only contain tool calls (no content text)
  - [x] 14.9 Show loading spinner with "Thinking..." text when processing user message
  - [x] 14.10 Implement API quota error banner (persist for one render cycle)

- [x] 15. Job Intake Step 2 - Chat Message Persistence

  - [x] 15.1 Create API hook/function to fetch chat messages from `/api/v1/jobs/{jobId}/intake-session/{sessionId}/messages?step=2`
  - [x] 15.2 Store messages in React state as array with structure: `{ role: "user" | "assistant" | "tool", content: string, tool_calls?: array, tool_call_id?: string }`
  - [x] 15.3 Load messages on page load, initialize empty array if none exist
  - [x] 15.4 Create API hook/function to save message history via POST to same endpoint
  - [x] 15.5 Save full message history to database after each exchange
  - [x] 15.6 Verify messages persist across page refreshes and navigation

- [x] 16. Job Intake Step 2 - Chat API Integration and Tool Calls

  - [x] 16.1 Create API hook/function for POST to `/api/v1/workflows/resume-chat` with ResumeChatRequest payload
  - [x] 16.2 Format work_experience string by fetching user experiences and formatting
  - [x] 16.3 Handle response: extract `message` (AI response dict) and `version_id` (if tool created version)
  - [x] 16.4 Show tool messages after execution completes (backend handles execution)
  - [x] 16.5 If `version_id` present, update selected version and refresh version list
  - [x] 16.6 Append AI response to message history and save to database
  - [x] 16.7 Handle quota errors: show banner, don't remove user message from history
  - [x] 16.8 Handle other errors: show generic error toast, don't remove user message

- [x] 17. Job Intake Step 2 - Tab Structure and Content Tabs

  - [x] 17.1 Create shadcn Tabs component with 5 tabs: "Job", "Gap Analysis", "Stakeholder Analysis", "Content", "Preview"
  - [x] 17.2 Set fixed-height scrollable container (600px) for each tab content area
  - [x] 17.3 Store selected tab index in component state (persists across version changes)
  - [x] 17.4 Implement Job tab: display job title and company as "**{title}** at **{company}**", show job description markdown, handle empty state
  - [x] 17.5 Implement Gap Analysis tab: display markdown from intake session, parse JSON if needed, handle missing error
  - [x] 17.6 Implement Stakeholder Analysis tab: display markdown from intake session, parse JSON if needed, handle missing error

- [x] 18. Job Intake Step 2 - Version Navigation UI

  - [x] 18.1 Create version navigation component for Content and Preview tabs (top row, right-aligned)
  - [x] 18.2 Add left arrow button (disabled if current version is v1 - oldest)
  - [x] 18.3 Add version dropdown showing "v{N}" format, descending order (newest first), include "(pinned)" suffix
  - [x] 18.4 Add right arrow button (disabled if current version is latest)
  - [x] 18.5 Add pin/unpin button (icon-only, filled if pinned, outline if not, primary variant if pinned)
  - [x] 18.6 Add three-dot menu with "Copy resume" and "Download resume" options (download only enabled if pinned)
  - [x] 18.7 Synchronize version navigation between Content and Preview tabs (shared state)

- [x] 19. Job Intake Step 2 - Version Selection and Loading Logic

  - [x] 19.1 Create API hook to fetch versions via `/api/v1/jobs/{jobId}/resumes/versions`
  - [x] 19.2 Set default selection to latest version (highest version_index) on page load
  - [x] 19.3 Store selected version ID in component state
  - [x] 19.4 Implement version change handler: check for unsaved changes, show save/discard dialog if dirty
  - [x] 19.5 Load version's `resume_json` into draft state when version changes
  - [x] 19.6 Track `loaded_version_id` for dirty state comparison
  - [x] 19.7 Initialize empty draft with user's basic info if no versions exist

- [x] 20. Job Intake Step 2 - Version Pinning and Unpinning

  - [x] 20.1 Check if unpin endpoint exists (`/api/v1/jobs/{jobId}/resumes/unpin`), create DELETE endpoint if missing
  - [x] 20.2 Implement pin button click handler: POST to pin endpoint if not pinned, DELETE to unpin endpoint if pinned
  - [x] 20.3 Refresh version list after pinning/unpinning
  - [x] 20.4 Update UI to show pin status (button state, dropdown suffix)
  - [x] 20.5 Show toast notification: "Pinned canonical resume." or "Unpinned resume."
  - [x] 20.6 Check canonical version via `/api/v1/jobs/{jobId}/resumes/current` to enable/disable Next button

- [x] 21. Job Intake Step 2 - Shared Resume Editor Component

  - [x] 21.1 Extract resume editing UI from `web/src/components/job-detail/ResumeTab.tsx` to shared component
  - [x] 21.2 Create reusable component at `web/src/components/resume/ResumeEditor.tsx`
  - [x] 21.3 Implement tab structure: Profile, Experience, Education, Certifications, Skills tabs
  - [x] 21.4 Update ResumeTab.tsx to use shared ResumeEditor component
  - [x] 21.5 Ensure component accepts props for resume data, update handler, and read-only state

- [x] 22. Job Intake Step 2 - Content Tab Resume Editing Interface

  - [x] 22.1 Add version navigation row at top of Content tab (use shared component)
  - [x] 22.2 Add action buttons row below version navigation (right-aligned): Discard and Save buttons
  - [x] 22.3 Implement Discard button: always enabled, disabled if not dirty, reverts draft to loaded version
  - [x] 22.4 Implement Save button: primary variant, disabled if not dirty
  - [x] 22.5 Create API hook for POST to `/api/v1/jobs/{jobId}/resumes/versions` with ResumeVersionCreate payload
  - [x] 22.6 After save: update selected version, reset dirty state, show toast, trigger PDF preview refresh
  - [x] 22.7 Add scrollable container (600px height) with ResumeEditor component below buttons

- [x] 23. Job Intake Step 2 - Dirty State Tracking

  - [x] 23.1 Implement dirty state tracking: compare current draft JSON string with loaded version's JSON string
  - [x] 23.2 Update dirty state whenever any form field changes in ResumeEditor
  - [x] 23.3 Handle empty state: if no loaded version, consider dirty if any content exists
  - [x] 23.4 Use dirty state to control Discard and Save button enabled states
  - [x] 23.5 Show unsaved changes dialog when navigating away with dirty state

- [x] 24. Job Intake Step 2 - Preview Tab PDF Display

  - [x] 24.1 Add version navigation row at top of Preview tab (synchronized with Content tab)
  - [x] 24.2 Install react-pdf library
  - [x] 24.3 Create scrollable PDF viewer container (600px height)
  - [x] 24.4 Create API hook to fetch PDF via GET `/api/v1/jobs/{jobId}/resumes/versions/{versionId}/preview` with query params
  - [x] 24.5 Implement PDF display using react-pdf library
  - [x] 24.6 Update PDF preview when: new draft saved (user or AI), version changed (NOT real-time on input)
  - [x] 24.7 Handle empty state: show info message if no versions exist
  - [x] 24.8 Handle PDF rendering errors: show error message

- [x] 25. Job Intake Step 2 - Action Buttons and Navigation

  - [x] 25.1 Implement Back button: navigate to Step 1 (`/intake/{jobId}/details`), don't clear state
  - [x] 25.2 Implement Skip button: mark Step 2 completed, navigate to Step 3, set empty proposals array
  - [x] 25.3 Implement Next button: primary variant, disabled until version is pinned
  - [x] 25.4 On Next click: call experience extraction workflow (POST `/api/v1/workflows/experience-extraction`)
  - [x] 25.5 Store proposals in state/store for Step 3, mark Step 2 completed, navigate to Step 3
  - [x] 25.6 Handle quota errors gracefully: allow continuing to Step 3 with empty proposals

- [x] 26. Job Intake Step 2 - Error Handling and State Management

  - [x] 26.1 Implement API quota error banner at top of chat interface (persist one render cycle)
  - [x] 26.2 Implement network error handling: show toast error, allow retry
  - [x] 26.3 Implement validation error (422) handling: show toast with specific message, ensure payload matches schema
  - [x] 26.4 Implement missing data error handling: show error in main content area with action to go back
  - [x] 26.5 Use shadcn Sonner toast for all user feedback (success, error, info)
  - [x] 26.6 Show spinners during API calls, disable relevant buttons during operations
  - [x] 26.7 Set up React useState for: chat messages, selected version ID, draft resume data, loaded version ID, dirty state, selected tab index, versions list, loading states
  - [x] 26.8 Set up React Query for: job data, intake session, versions list, user data, experiences

- [x] 27. Job Intake Step 2 - Initialization and Data Loading
  - [x] 27.1 Implement initialization sequence: fetch job data, intake session, validate analyses, fetch user data, fetch versions, load chat messages, set default version, load draft state
  - [x] 27.2 Show loading spinner during initialization
  - [x] 27.3 Handle errors at each initialization step appropriately
  - [x] 27.4 Validate gap_analysis and stakeholder_analysis exist, show error if missing
  - [x] 27.5 Regenerate TypeScript types from OpenAPI schema if needed before implementation
  - [x] 27.6 Ensure all request payloads match API schema exactly (ResumeChatMessage, ResumeChatRequest, ResumeVersionCreate)
