# Home Page

## Statistics Layout

For a cleaner interface with no cards adding visual clutter:

**Primary Stats Row (Top):**

- Three main stats displayed in a single row with large, bold numbers
- Each stat shows the number prominently with a title underneath
- Stats: "Jobs Applied (Last 7 Days)", "Jobs Applied (Last 30 Days)", "Days Since Last Application"
- Use text-3xl or larger for numbers, standard text for titles

**Secondary Stats Row (Below Primary):**

- Four columns displayed in a significantly smaller format
- Use regular text or medium-sized text (one size up from regular)
- Stats: "Total Jobs Applied", "Total Jobs Saved", "Interviews Scheduled", "Offers Received"
- Less visual emphasis than primary stats

**Application Activity Heatmap:**

- Display below the statistics sections
- Reduce gaps between sections so everything fits on the main dashboard more compactly

## Days Since Last Application

- Calculate as the number of days between today and the most recent `applied_at` date
- Display format:
  - "Today" if 0 days
  - "1 day" if singular
  - "X days" if plural
  - "N/A" if no applications exist

## Activity Heatmap Tooltips

- Use the react-calendar-heatmap library's built-in functionality for tooltips
- Implement `titleForValue` function to generate title attribute for each square
- Implement `tooltipDataAttrs` function (or object) to set data attributes for tooltip generation
- Tooltip should display: date (formatted) and number of applications (e.g., "January 15, 2024 - 3 applications")
- Reference: https://github.com/kevinsqi/react-calendar-heatmap documentation

# Profile Page

## Profile Information Card

- Fix excessive gap above the user's name (reduce padding/spacing in CardContent)
- Move edit button inside the profile information card
- Edit button should be icon-only (no "Edit Profile" text), matching work experience edit button style
- Place edit icon button in the top-right corner of the card

## LinkedIn and GitHub Icons

- Use lucide-react icons for LinkedIn and GitHub (if available)
- Display icons next to the respective URLs in the profile information section
- Icons should be clickable links that open URLs in a new tab

## Achievements Section

- Change from global expand/collapse to individual expand/collapse per achievement
- Each achievement has its own expand/collapse button
- Default state: collapsed (show only title)
- Expanded state: show title and full content
- Remove the global expand/collapse button
- Use accordion-style component for each achievement
- This makes it obvious that achievements exist even when collapsed

## Work Experience Card Improvements

- Reduce gap between company name and date/location
- Add subheaders for visual distinction:
  - "Company Overview" subheader
  - "Role Overview" subheader
  - "Skills" subheader
- Make date and location more compact:
  - Display on single line, separated by bullet or comma
  - Use smaller text size to reduce vertical space
- Improve overall spacing to reduce visual clutter

# Jobs Page

## Actions Button Fix

- The actions button (triple dot / MoreVertical icon) currently navigates to the job detail page when clicked
- Fix: Add `onClick={(e) => e.stopPropagation()}` to prevent navigation
- Ensure the dropdown/popover menu opens without navigating to the job detail page
- Actions button should only trigger the dropdown menu, not navigation

# Job - Notes

## Layout and Column Structure

- Two-column layout: 60% width for notes list (left), 40% width for add note form (right)
- Use CSS Grid: `grid-template-columns: 60% 40%` or Tailwind equivalent
- Add vertical divider line between the two columns
- Ensure responsive behavior (stack vertically on mobile)

## Add New Note Section

- Remove card wrapper around add note section (no card styling)
- Remove "Add New Note" subheader
- Placeholder text: Change from "write a note..." to "add new note here..."
- Fixed height textarea: Height should fit on screen but not go below 200px
- Textarea should be scrollable when content exceeds the fixed height
- Buttons:
  - Rename to "Save" and "Discard" (no icons, text only)
  - Position buttons above the textarea input (not below)
  - Save button: Enabled only when there is content
  - Discard button: Always enabled

## Saved Notes Display

- Date positioning: Move date to the top row, displayed as title on the left side
- Action buttons positioning: Move edit and delete buttons to top-right corner
- Button styling:
  - Use icon-only buttons (no text labels)
  - Delete icon should be red or styled to indicate destructive action
  - Edit icon standard styling

## Note Content Truncation

- Truncate note content after 500 characters
- Show "..." after truncated text
- Add "Show more" / "Show less" toggle to expand/collapse full content
- Truncation applies only to content, not the date/title

## Edit Mode Behavior

- When editing a note:
  - Replace edit/delete buttons with Discard and Save buttons at the top
  - Discard button: Always enabled, exits edit mode when clicked
  - Save button: Enabled only when content has changed from original note (dirty state)
  - Clicking Discard exits edit mode and discards any unsaved changes

## Sticky Add Note Section

- Keep add note form visible while scrolling using CSS `position: sticky`
- Set appropriate `top` offset to account for header/navigation
- Ensure it doesn't overlap with fixed headers or navigation elements
- Test scrolling behavior to confirm it stays visible at all scroll positions

# Job Intake

## Step 1

### Header

- Header text: "Job Intake: Step 1 of 3 - Job Details"
- Remove subtitle "Step 1 of 3" (already included in header)
- Remove descriptive text "Enter the Job description and details..."

### Field Layout

- Single row above job description containing:
  - Favorite star icon (positioned first/in front)
  - Job Title input (flex-1)
  - Company Name input (flex-1)
- Remove all field subtitles/descriptions (they add visual clutter)
- Replace with tooltips on hover for additional information:
  - Job Title tooltip: "The title of the position you're applying for"
  - Company Name tooltip: "The name of the company offering this position"
  - Favorite tooltip: "Mark this job as favorite for easy access"

### Parse Info Button

- Keep button positioned in bottom-right corner above the job description textarea
- Add tooltip: "Automatically extract job title and company name from the job description"
- Use shadcn Tooltip component for hover tooltip

### Next Button

- Change button text from "Next: Select Experience" to "Next"
- Keep same functionality and navigation behavior

## Step 2

### Overview

The current Step 2 implementation is incorrect and doesn't match the Streamlit app workflow. This step needs to be completely rebuilt to replicate the Streamlit app functionality within Next.js.

### Page Layout and Structure

- **Full-height layout** with header and action buttons at bottom
- **Header row**:
  - Left side: "Job Intake: Step 2 of 3 - Experience & Resume Development" (text)
  - Right side: Copy job context button (tertiary style)
- **Two-column grid layout**:
  - Left column: 40% width - Chat interface
  - Right column: 60% width - Tabs interface
  - Columns fill available vertical space: `calc(100vh - header height - action buttons height)`
- **Bottom action buttons row**:
  - Left side: Back button
  - Right side: Skip button and Next button (Next disabled until version is pinned)
- **Responsive behavior**: Stack columns vertically on mobile (< 768px width)

### Chat Interface Implementation

- **Component library**: Use shadcn-chatbot-kit components directly (https://shadcn-chatbot-kit.vercel.app/docs)
- **Chat title**: "Resume Agent" displayed above message container
- **Message container**: Fixed-height scrollable container (550px) for message history
- **Chat input**: Positioned at bottom with placeholder "Ask for resume changes..."
- **Message display**:
  - User messages: Right-aligned with distinct styling
  - Assistant messages: Left-aligned with distinct styling
  - Tool messages: Subtle styling, shown as captions
  - Skip rendering assistant messages that only contain tool calls (no content text)
  - Show tool messages after execution is finished (not immediately when tool is called)
- **Loading state**: Show spinner with "Thinking..." text when processing user message
- **Error handling**:
  - Show API quota error banner if quota exceeded (persist for one render cycle)
  - Show generic error toast for other failures
  - Do not remove user message from history on error

### Chat Message Persistence and Loading

- **On page load**: Fetch chat messages from `/api/v1/jobs/{jobId}/intake-session/{sessionId}/messages?step=2`
- **Message storage**: Store messages in React state as array of objects with structure:
  - `role`: "user" | "assistant" | "tool"
  - `content`: string
  - `tool_calls`: optional array (for assistant messages)
  - `tool_call_id`: optional string (for tool messages)
- **After each exchange**: Save full message history to database via POST to same endpoint
- **Persistence**: Messages persist across page refreshes and navigation
- **Initialization**: Initialize empty array if no messages exist

### Chat API Integration and Tool Call Handling

- **On user message submit**: POST to `/api/v1/workflows/resume-chat` with payload:
  - `messages`: Full chat history array (ResumeChatMessage format)
  - `job_id`: Current job ID
  - `selected_version_id`: Currently selected version ID (null if none exists)
  - `gap_analysis`: Markdown string from intake session
  - `stakeholder_analysis`: Markdown string from intake session
  - `work_experience`: Formatted work experience string (fetch user experiences and format)
- **Response handling**:
  - Response includes `message` (AI response dict) and `version_id` (new version ID if tool created one)
  - If response contains `tool_calls` in message: Backend automatically executes tool calls and returns result
  - Show tool messages after execution completes (not immediately when tool is called)
  - If `version_id` is present: Update selected version to new version ID and refresh version list
- **Message history**: Append AI response to message history and save to database
- **Error handling**:
  - Show quota error banner for quota exceeded errors
  - Show generic error toast for other failures
  - Do not remove user message from history on error

### Right Column Tab Structure

- **Tab component**: Use shadcn Tabs component with 5 tabs
- **Tab order**: "Job", "Gap Analysis", "Stakeholder Analysis", "Content", "Preview"
- **Tab content area**: Fixed-height scrollable container (600px) for each tab
- **Tab persistence**: Selected tab persists across version changes (store in component state)

### Job Tab Content

- **Display format**:
  - Job title and company on same line: "**{title}** at **{company}**" (bold formatting)
  - Below: Full job description as markdown text
- **Empty state**: If no description, show info message "No job description available."
- **Content**: Scrollable within tab container
- **Data source**: Fetch job data from `/api/v1/jobs/{jobId}` on page load

### Gap Analysis Tab Content

- **Display**: Gap analysis markdown from intake session
- **Data source**: Fetch from intake session `gap_analysis` field (stored as JSON string, parse if needed)
- **Rendering**: Render markdown with proper formatting
- **Error state**: If missing, show error "Unable to load analyses. Please restart intake flow."
- **Content**: Scrollable within tab container

### Stakeholder Analysis Tab Content

- **Display**: Stakeholder analysis markdown from intake session
- **Data source**: Fetch from intake session `stakeholder_analysis` field (stored as JSON string, parse if needed)
- **Rendering**: Render markdown with proper formatting
- **Error state**: If missing, show error "Unable to load analyses. Please restart intake flow."
- **Content**: Scrollable within tab container

### Version Navigation UI (Content and Preview Tabs)

- **Location**: Top row of Content and Preview tabs
- **Layout**: Horizontal container, right-aligned, containing:
  - Left arrow button (disabled if current version is v1 - oldest)
  - Version dropdown (shows "v{N}" format, descending order newest first, includes "(pinned)" suffix)
  - Right arrow button (disabled if current version is latest)
  - Pin/unpin button (icon-only, filled icon if pinned, outline if not pinned, primary variant if pinned, secondary if not)
  - Three-dot menu with:
    - "Copy resume" option (copies resume text to clipboard)
    - "Download resume" option (only enabled if version is pinned, downloads PDF)
- **Synchronization**: Version navigation is synchronized between Content and Preview tabs (changing version in one updates the other)

### Version Selection and Loading Logic

- **On page load**: Fetch all versions via `/api/v1/jobs/{jobId}/resumes/versions`
- **Default selection**: Latest version (highest version_index)
- **State management**: Store selected version ID in component state
- **Version change**: When version changes via navigation controls:
  - If draft has unsaved changes: Prompt user to save or discard first (show dialog)
  - Load version's `resume_json` into draft state
- **Draft state**: Parsed ResumeData object stored in component state
- **Dirty tracking**: Track `loaded_version_id` to compare for dirty state
- **Empty state**: If no versions exist, initialize empty draft with user's basic info (name, email, phone, LinkedIn from user profile)

### Version Pinning and Unpinning Functionality

- **Pin button click**:
  - If version is not pinned: POST to `/api/v1/jobs/{jobId}/resumes/{versionId}/pin`
  - If version is pinned: POST to `/api/v1/jobs/{jobId}/resumes/unpin` (create endpoint if it doesn't exist)
- **After pinning/unpinning**:
  - Refresh version list
  - Update UI to show pin status
  - Show toast notification: "Pinned canonical resume." or "Unpinned resume."
- **Next button**: Enabled only when a version is pinned (check canonical version via `/api/v1/jobs/{jobId}/resumes/current`)
- **API endpoint**: Check if unpin endpoint exists (`/api/v1/jobs/{jobId}/resumes/unpin`), create if missing (DELETE method)

### Content Tab - Resume Editing Interface

- **Version navigation**: Top row with version controls (see Version Navigation UI section)
- **Action buttons row**: Below version navigation, right-aligned:
  - Discard button: Always enabled, disabled if not dirty, reverts draft to loaded version's JSON
  - Save button: Primary variant, disabled if not dirty
- **Save functionality**: Creates new version via POST to `/api/v1/jobs/{jobId}/resumes/versions` with:
  - `template_name`: From selected version (or default template if no versions)
  - `resume_json`: Current draft JSON
  - `event_type`: "save"
  - `parent_version_id`: Selected version ID
- **After save**:
  - Update selected version to new version
  - Reset dirty state
  - Show toast "Changes saved as new version!"
  - Update PDF preview (trigger refresh)
- **Edit form**: Below buttons, scrollable container (600px height) with resume editing tabs

### Resume Edit Form - Shared Component Reuse

- **Component location**: Extract resume editing UI from `web/src/components/job-detail/ResumeTab.tsx` to shared component
- **Shared component**: Create reusable component at `web/src/components/resume/ResumeEditor.tsx` or similar
- **Tab structure**: Use tabs instead of collapsible sections (different from Streamlit):
  - Profile tab
  - Experience tab
  - Education tab
  - Certifications tab
  - Skills tab
- **Reuse**: Use same component in both:
  - Job Intake Step 2 Content tab
  - Job Detail page Resume tab
- **Tab content**: Each tab contains form fields for editing that section (see ResumeTab.tsx for reference)

### Resume Edit Form Sections

- **Profile tab**:
  - Full Name (text input)
  - Title (text input, with tooltip icon)
  - Email (text input)
  - Phone Number (text input)
  - LinkedIn URL (text input, optional)
  - Professional Summary (textarea, 250px height, with tooltip icon)
- **Experience tab**:
  - List of experience items, each with:
    - Title (text input)
    - Company (text input)
    - Location (text input)
    - Start Date (date input)
    - End Date (date input, optional)
    - Points (textarea, one per line, 350px height, with tooltip icon)
    - Delete button (icon-only, right-aligned)
  - "Add Experience" button at bottom (opens inline form or modal)
- **Education tab**:
  - List of education items, each with:
    - Institution (text input)
    - Degree (text input)
    - Major (text input)
    - Graduation Date (date input)
    - Delete button (icon-only, right-aligned)
  - "Add Education" button at bottom (opens inline form or modal)
- **Certifications tab**:
  - List of certification items, each with:
    - Title (text input)
    - Date (date input)
    - Delete button (icon-only, right-aligned)
  - "Add Certification" button at bottom (opens inline form or modal)
- **Skills tab**:
  - Textarea accepting commas and/or newlines
  - Formatted one per line
  - 400px height
  - Tooltip icon

### Dirty State Tracking

- **Tracking method**: Compare current draft JSON string with loaded version's JSON string
- **Update trigger**: Update dirty state whenever any form field changes
- **Empty state**: If no loaded version (first version), consider dirty if any content exists (name, title, summary, experience, education, certifications, or skills)
- **UI indicators**: Dirty state controls Discard and Save button enabled states

### Preview Tab - PDF Display

- **Version navigation**: Top row with version controls (same as Content tab, synchronized)
- **PDF viewer**: Below version navigation, scrollable PDF viewer container (600px height)
- **PDF fetching**: Fetch PDF via GET `/api/v1/jobs/{jobId}/resumes/versions/{versionId}/preview` with query params:
  - `resume_json`: Current draft JSON (or selected version JSON if not dirty)
  - `template_name`: Selected version template name
- **PDF library**: Use react-pdf library for PDF display
- **Update trigger**: PDF preview updates when:
  - New draft is saved (by user or AI)
  - Version is changed
  - NOT updated in real-time as user inputs information
- **Empty state**: If no versions exist, show info message "No resume version available yet. Use the chat or edit the Resume Content tab to create one."
- **Error handling**: Show error message "Failed to render PDF preview" on rendering errors

### Action Buttons (Bottom of Page)

- **Layout**: Two-column layout
  - Left side: Back button
  - Right side: Skip button and Next button
- **Back button**: Navigates to Step 1 (`/intake/{jobId}/details`), does not clear state
- **Skip button**:
  - Marks Step 2 as completed
  - Navigates to Step 3
  - Sets empty proposals array
- **Next button**:
  - Primary variant
  - Disabled until a version is pinned
  - On click:
    - Calls experience extraction workflow: POST `/api/v1/workflows/experience-extraction` with chat messages and experience IDs
    - Stores proposals in state/store for Step 3
    - Marks Step 2 as completed
    - Navigates to Step 3 (`/intake/{jobId}/proposals`)
    - Handles quota errors gracefully (allows continuing to Step 3 with empty proposals)

### Error Handling and User Feedback

- **API quota errors**: Show persistent banner at top of chat interface, do not remove user message from history
- **Network errors**: Show toast error, allow retry
- **Validation errors (422)**: Show toast with specific error message, ensure request payload matches API schema exactly
- **Missing data errors**: Show error message in main content area with action to go back (no job, no session, no analyses)
- **User feedback**: Use shadcn Sonner toast for all user feedback (success, error, info)
- **Loading states**: Show spinners during API calls, disable relevant buttons during operations

### State Management Approach

- **React useState** for:
  - Chat messages array
  - Selected version ID
  - Draft resume data (ResumeData object)
  - Loaded version ID (for dirty tracking)
  - Dirty state boolean
  - Selected tab index
  - Versions list array
  - Loading states (chat loading, save loading, etc.)
- **React Query** for:
  - Job data fetching
  - Intake session data fetching
  - Versions list fetching
  - User data fetching
  - Experiences fetching (for work_experience formatting)
- **Persistence**:
  - Chat messages saved to database after each exchange
  - Version selection could use URL params or localStorage

### TypeScript Types and API Integration

- **Type generation**: Use auto-generated types from OpenAPI schema (`web/src/types/api.ts`)
- **Before implementation**: Regenerate types if schema changed (`npm run generate:types` or equivalent)
- **API client**: Use typed API client functions from `web/src/lib/api/` modules
- **Request validation**: Ensure all request payloads match API schema exactly:
  - ResumeChatMessage: `{ role: string, content: string, tool_calls?: array, tool_call_id?: string }`
  - ResumeChatRequest: Includes all required fields with correct types
  - ResumeVersionCreate: Includes template_name, resume_json, event_type, parent_version_id
- **Error handling**: Validate types at compile time, handle runtime validation errors gracefully

### Initialization and Data Loading Sequence

- **On page load** (in order):
  1. Fetch job data (`/api/v1/jobs/{jobId}`)
  2. Fetch intake session (`/api/v1/jobs/{jobId}/intake-session`)
  3. Validate gap_analysis and stakeholder_analysis exist (show error if missing)
  4. Fetch user data (for default draft initialization)
  5. Fetch versions list (`/api/v1/jobs/{jobId}/resumes/versions`)
  6. Load chat messages (`/api/v1/jobs/{jobId}/intake-session/{sessionId}/messages?step=2`)
  7. Set default selected version (latest or null)
  8. Load draft state from selected version (or initialize empty draft)
- **Loading state**: Show loading spinner during initialization
- **Error handling**: Handle errors at each step appropriately

### Workflow Reference

- **Primary reference**: `api/app/dialog/job_intake/step2_experience_and_resume.py`
- **Understanding required**: Complete flow from chat input → tool calls → resume generation → version management
- **UI adaptation**: Match UI/UX patterns while adapting to Next.js/React component structure
- **Key differences from Streamlit**:
  - Use tabs for resume editing sections instead of collapsible accordions
  - Reuse shared resume editing component from job detail page
  - Synchronized version navigation between Content and Preview tabs
It's the intake/new route. It is not displaying what was described in this document. 