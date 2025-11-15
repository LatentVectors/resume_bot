# Job Intake

## General

### Remove Layout File

**Delete:** `apps/web/src/app/intake/[jobId]/layout.tsx`

The layout file contains progress indicators (progress bar and numbered step indicators) that are redundant. Each page will implement its own container wrapper instead.

### Fixed Footer Navigation

Each step page should implement its own fixed footer at the bottom of the viewport containing navigation buttons. The footer should:

- Use CSS fixed positioning: `fixed bottom-0 left-0 right-0 bg-background border-t z-50 p-4`
- Add bottom padding to page content (`pb-24`) to prevent content from being hidden behind footer
- Replace existing navigation buttons in each form (not supplement them)

**Button Configuration per Step:**

- **Step 1 (Details):** Cancel, Next
- **Step 2 (Experience):** Back, Skip, Next
- **Step 3 (Proposals):** Back, Finish

**Container Widths:**

- Step 1: `max-w-4xl` (form-focused content)
- Step 2: `max-w-6xl` (two-column layout needs more space)
- Step 3: `max-w-4xl` (proposal cards)

### Navigation Button Behaviors

**Back Button:**

- Step 2: Navigate to `/intake/{jobId}/details`
- Step 3: Navigate to `/intake/{jobId}/experience`
- No unsaved changes check required

**Skip Button (Step 2 only):**

- Navigates directly to `/intake/{jobId}/proposals`
- Triggers the AI to generate experience proposals
- Same behavior as "Next" button, except "Next" is only enabled when a resume draft has been saved
- Skip allows bypassing the resume draft requirement

**Next Button:**

- Step 1: Navigate to `/intake/{jobId}/experience`
- Step 2: Navigate to `/intake/{jobId}/proposals` (enabled only after saving a resume draft)

**Finish Button (Step 3):**

- Navigate to `/jobs/{jobId}` (job detail page)
- Mark intake workflow as complete

## Step 1 - Job Details

**File:** `apps/web/src/components/intake/JobDetailsForm.tsx`

### Layout Changes

- Remove the Card wrapper around the form (keep only the form content)
- The page title "Job Intake: Step 1 of 3 - Job Details" should remain but not be wrapped in a card

### Form Field Updates

- Add `<FormLabel>` components for Job Title, Company Name, and Job Description fields
- Job Description textarea: Change from `min-h-[400px] resize-y` to `h-[250px] resize-none overflow-y-auto`

### Tooltip Configuration

- Update `TooltipProvider` to add `delayDuration={500}` for a medium hover delay before tooltips appear

### Navigation Flow Fix

**Current behavior:** `/intake/new/details` → creates job → navigates to `/intake/{jobId}/details` (redundant)
**New behavior:** `/intake/new/details` → creates job → navigates directly to `/intake/{jobId}/experience`

**Implementation:** In `apps/web/src/app/intake/new/details/page.tsx`, change the `handleJobCreated` function to navigate to `/intake/${jobId}/experience` instead of `/intake/${jobId}/details`.

## Step 2 - Experience & Resume Development

**File:** `apps/web/src/app/intake/[jobId]/experience/page.tsx`

### Layout Changes

- Change container from `max-w-4xl` to `max-w-6xl` to increase content width
- Place a vertical divider between the two columns using shadcn/ui `Separator` component with `orientation="vertical"`
- Remove card wrapper from right column content

### Actions Menu

- Replace the copy button with a three-dot menu button (MoreVertical icon from lucide-react)
- Use shadcn/ui `Popover` component for the menu
- Initial action: "Copy Job Context" (more actions may be added later)

**Implementation:**

```tsx
<Popover>
  <PopoverTrigger asChild>
    <Button variant="ghost" size="icon">
      <MoreVertical className="h-4 w-4" />
    </Button>
  </PopoverTrigger>
  <PopoverContent>
    <Button variant="ghost" onClick={handleCopyJobContext}>
      Copy Job Context
    </Button>
  </PopoverContent>
</Popover>
```

### Markdown Rendering

**Gap Analysis and Stakeholder Analysis** are currently rendering as plain text. They need to be rendered as HTML from markdown.

- Use `react-markdown` with `remark-gfm` plugin
- Apply appropriate styling to maintain readability (use Tailwind typography or custom classes)
- **Error Handling:** If markdown rendering fails, fall back to displaying plain text

### Chat Interface Fixes

**Problem:** Messages push the input down, requiring excessive scrolling.
**Solution:**

- Make the chat messages container a fixed height calculated based on viewport height
- Input should remain fixed at the bottom of the chat area
- Messages container should be scrollable with `overflow-y-auto`
- Auto-scroll to bottom when new messages arrive (check if ChatInterface component has built-in support)

### Content Tab - Conditional UI

**Current:** Save and Discard buttons always visible, creating clutter when disabled.
**New behavior:**

- When content is NOT dirty (no edits): Show version navigation row (Previous, Next, Version Select, Pin, Actions)
- When content IS dirty (user has edited): Hide version navigation row, show Save and Discard buttons in its place
- When user clicks Save or Discard: Restore version navigation row

**Version Navigation Restriction:**

- Unsaved changes should only prevent version navigation (changing to a different version)
- User can still switch between tabs (Job Context, Gap Analysis, PDF Preview) with unsaved changes
- If user attempts to navigate to a different version with unsaved changes, show the existing unsaved changes dialog

### PDF Preview Scaling

**Problem:** PDF preview is not scaled to fit container width.
**Solution:** Configure the PDF viewer to fit the width of its container so the full page is visible and user can scroll vertically to view the entire document.

## Step 3 - Experience Updates

**File:** `apps/web/src/app/intake/[jobId]/proposals/page.tsx`

### Page Title

Change the title to follow the pattern of other steps:

- Main title: "Job Intake: Step 3 of 3 - Experience Updates"
- Add a subtitle describing the purpose

### Proposals Layout

**Remove** the Card wrapper around the entire "Experience Proposals" section.

- The section title should appear directly on the page (not in a card)
- Individual proposal cards should remain as Card components
- Keep the existing individual proposal card styling

### Empty State

When no proposals are generated, display a centered message: "No updates found."

### Complete Button

Change the button text from "Complete Intake Workflow" to "Finish"

- Keep the button at the bottom of the page
- Maintain current functionality (navigate to job detail page)

# Job Detail Page Changes

## Resume Tab

**File:** `apps/web/src/components/job-detail/ResumeTab.tsx`

### Shared Component Extraction

Extract the following UI components from `apps/web/src/app/intake/[jobId]/experience/page.tsx` into a shared location so both Step 2 and the Resume Tab can use them:

- Chat interface component
- Content/Preview tabs structure
- Gap Analysis display
- Stakeholder Analysis display
- Version navigation logic
- Resume editing interface

Suggested location: `apps/web/src/components/intake/` or `apps/web/src/components/shared/`

### Resume Tab Functionality

The Resume Tab should provide the same functionality as Step 2 (Experience & Resume Development), including:

- **Chat Interface:** Full chat with message history from the intake workflow
- **Tabs:** Job Context, Gap Analysis, Stakeholder Analysis, Content, Preview
- **Resume Editing:** All content editing capabilities from Step 2
- **Version History:** Prepopulated with all versions created during intake
- **All Step 2 improvements:** Markdown rendering, action menu, conditional save/discard UI, PDF scaling, etc.

### Key Differences from Step 2

- **No fixed footer:** The Resume Tab should NOT have the fixed footer navigation (that's specific to intake workflow)
- **No step title:** Should not display "Job Intake: Step X of 3" heading
- Context: User is viewing an existing job, not actively in the intake flow

### Data Continuity

All data from the intake session should be accessible:

- Message history from Step 2 chat
- All resume versions created during intake
- Gap analysis and stakeholder analysis generated during intake
- Current pinned/canonical resume version

## Notes Tab

**File:** `apps/web/src/components/job-detail/NotesTab.tsx`

### Scrolling Behavior

**Problem:** When many notes exist, the page becomes very tall and the "add note" form is pushed far down.

**Solution:**

- Make the left column (notes list) scrollable with a max-height
- Right column (new note form) should remain sticky at the top of its column
- This allows users to scroll through notes while keeping the input form accessible

**Implementation:**

- Add `max-h-[calc(100vh-200px)] overflow-y-auto` to the left column (notes list)
- The 200px offset accounts for page header, tab navigation, and margins
- Right column already has `lg:sticky lg:top-20` which should continue to work

# Technical Implementation Details

## Dependencies

Add the following npm packages to `apps/web`:

```bash
npm install react-markdown remark-gfm
```

**Purpose:**

- `react-markdown`: Render markdown content as HTML for Gap Analysis and Stakeholder Analysis
- `remark-gfm`: GitHub Flavored Markdown support (tables, strikethrough, etc.)

## Shared Component Architecture

**Create:** `apps/web/src/components/intake/ExperienceResumeInterface.tsx`

This single composite component should encapsulate all the functionality from Step 2 Experience page. Both the intake Step 2 page and the Job Detail Resume Tab will import and use this component.

**Component Props:**

```typescript
interface ExperienceResumeInterfaceProps {
  jobId: number;
  showStepTitle?: boolean; // false for Resume Tab, true for Step 2
  showFooter?: boolean; // false for Resume Tab, true for Step 2
}
```

**The component should include:**

- Two-column layout (60/40 split with vertical divider)
- Left column: Chat interface, Job Context, Gap Analysis, Stakeholder Analysis tabs
- Right column: Content/Preview tabs with resume editing and PDF preview
- Actions menu with "Copy Job Context" option
- Version navigation with conditional save/discard UI
- Markdown rendering for analyses
- PDF scaling configuration
- Chat height calculation

### Utility Components

Extract these smaller components for reusability:

**Create:** `apps/web/src/components/intake/MarkdownRenderer.tsx`

- Wraps `react-markdown` with consistent configuration and error handling
- Falls back to plain text if markdown rendering fails
- Applies styling with `prose prose-sm` classes

**Create:** `apps/web/src/components/intake/ActionsMenu.tsx`

- Three-dot menu using Popover component
- Accepts array of action items as props
- Initially contains "Copy Job Context" action

**Create:** `apps/web/src/components/intake/PDFPreview.tsx`

- PDF viewer with automatic width scaling
- Uses container ref for dynamic sizing
- Handles loading and error states

## Markdown Rendering Implementation

Use `react-markdown` with `remark-gfm`:

```tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

<ReactMarkdown remarkPlugins={[remarkGfm]} className="prose prose-sm">
  {markdownContent}
</ReactMarkdown>;
```

Apply Tailwind typography plugin for styling or custom CSS classes.

## PDF Viewer Configuration

Use `react-pdf` with dynamic width calculation:

```tsx
const [containerWidth, setContainerWidth] = useState<number>(0);
const containerRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (containerRef.current) {
    setContainerWidth(containerRef.current.offsetWidth);
  }
}, []);

<Document file={pdfUrl} onLoadSuccess={onDocumentLoadSuccess}>
  <Page pageNumber={1} width={containerWidth} />
</Document>;
```

## Chat Height Calculation

Set chat messages container to: `h-[calc(100vh-400px)]`

Adjust the `400px` offset as needed to account for:

- Page header/navigation
- Tab navigation
- Chat input area
- Footer padding

The exact value should be fine-tuned during implementation.

## API Endpoint Requirements

### Chat History Management

Each job has one intake session. Need to verify or create API endpoints for:

**Required endpoints:**

- `GET /api/jobs/{job_id}/intake-session/messages` - Retrieve chat message history
- `POST /api/jobs/{job_id}/intake-session/messages` - Add new chat message
- `GET /api/jobs/{job_id}/intake-session` - Get intake session with all related data

If these endpoints don't exist, they need to be created in the API.

# Sprint Overview

## Goal

Improve the user experience of the job intake workflow by:

1. Reducing visual clutter and redundant UI elements
2. Improving navigation accessibility with fixed footers
3. Enhancing content readability with proper markdown rendering
4. Creating better spatial utilization and responsive layouts
5. Establishing code reusability between intake workflow and job detail pages

## User Stories

**As a user**, I want to always see navigation buttons at the bottom of the screen, so that I don't have to scroll to find them when filling out long forms.

**As a user**, I want the gap analysis and stakeholder analysis to be properly formatted, so that I can easily read and understand the AI-generated insights.

**As a user**, I want to access the same resume editing tools from both the intake workflow and the job detail page, so that I can continue working on my resume after completing the initial intake.

**As a user**, I want the chat interface to stay manageable, so that I don't lose the input box when the conversation gets long.

**As a user**, I want to skip generating a full resume draft during intake if I'm in a hurry, so that I can quickly get to the proposal review step.

## Implementation Priority

This sprint should be implemented in the following order:

1. **Step 1 Changes** - Simplest changes, good starting point

   - Remove card wrapper
   - Add form labels
   - Update tooltip delay
   - Fix navigation flow
   - Add fixed footer

2. **Install Dependencies** - Required before Step 2 changes

   - Add `react-markdown` and `remark-gfm`

3. **Create Utility Components** - Before refactoring Step 2

   - MarkdownRenderer
   - ActionsMenu
   - PDFPreview

4. **Step 2 Changes** - Most complex section

   - Layout updates (width, divider)
   - Implement actions menu
   - Add markdown rendering
   - Fix chat interface scrolling
   - Conditional save/discard UI
   - PDF scaling
   - Add fixed footer

5. **Extract Shared Component** - After Step 2 is working

   - Create ExperienceResumeInterface
   - Refactor Step 2 to use shared component

6. **Resume Tab Updates** - After shared component exists

   - Update ResumeTab to use ExperienceResumeInterface
   - Implement chat history loading
   - Verify data continuity

7. **Step 3 Changes** - Final intake step

   - Update title
   - Remove outer card
   - Update button text
   - Add fixed footer

8. **Notes Tab** - Independent from intake workflow

   - Add scrollable left column

9. **Cleanup** - After all changes working
   - Delete intake layout file
   - Remove unused code

## Files Changed

### Files to Delete

- `apps/web/src/app/intake/[jobId]/layout.tsx`

### Files to Create

- `apps/web/src/components/intake/ExperienceResumeInterface.tsx`
- `apps/web/src/components/intake/MarkdownRenderer.tsx`
- `apps/web/src/components/intake/ActionsMenu.tsx`
- `apps/web/src/components/intake/PDFPreview.tsx`

### Files to Modify

- `apps/web/src/app/intake/new/details/page.tsx`
- `apps/web/src/components/intake/JobDetailsForm.tsx`
- `apps/web/src/app/intake/[jobId]/details/page.tsx`
- `apps/web/src/app/intake/[jobId]/experience/page.tsx`
- `apps/web/src/app/intake/[jobId]/proposals/page.tsx`
- `apps/web/src/components/job-detail/ResumeTab.tsx`
- `apps/web/src/components/job-detail/NotesTab.tsx`

### API Files (if endpoints don't exist)

- `apps/api/api/routes/jobs.py` (or relevant route file)
  - Add endpoints for chat message history

## Edge Cases and Error Handling

### Navigation Edge Cases

**Direct Navigation to Step 2/3 Without Completing Previous Steps:**

- Current implementation uses intake session to track progress
- If user navigates directly to a step they haven't reached, they should be redirected to the appropriate step
- This behavior should be maintained

**Browser Back Button:**

- Should work naturally with route-based navigation
- No special handling required

### Data Loading Failures

**Intake Session Fails to Load on Resume Tab:**

- Display error message: "Unable to load intake session data"
- Provide option to retry or return to job overview
- Resume editing should still work with current resume data

**Chat Messages Fail to Load:**

- Display empty chat state
- Allow user to continue with new messages
- Show toast notification about the error

**Markdown Rendering Fails:**

- Automatically fall back to displaying plain text
- No error message needed (graceful degradation)

### State Management

**Unsaved Changes on Browser Refresh:**

- Current behavior: User loses unsaved changes
- Acceptable for this sprint
- Future enhancement: Local storage persistence

**Multiple Browser Tabs:**

- Changes in one tab won't reflect in others until refresh
- Acceptable limitation for this sprint

**Chat Messages:**

- Messages should be persisted to backend as they're sent
- No auto-save needed since messages are immediately saved

**Resume Drafts:**

- Only saved when user explicitly clicks Save or Generate
- No auto-save functionality in this sprint

## Testing Checklist

### Step 1 - Job Details

- [ ] Card wrapper removed, inputs layout correctly
- [ ] Form labels display for all three fields
- [ ] Tooltip delay is 500ms
- [ ] Job description textarea is 250px height with overflow scroll
- [ ] Fixed footer displays at bottom with Cancel and Next buttons
- [ ] Creating job navigates directly to `/intake/{jobId}/experience`
- [ ] Original navigation buttons removed from form

### Step 2 - Experience

- [ ] Container width is `max-w-6xl`
- [ ] Vertical separator displays between columns
- [ ] Three-dot actions menu displays and shows "Copy Job Context"
- [ ] Clicking "Copy Job Context" copies content to clipboard
- [ ] Gap Analysis renders as formatted markdown
- [ ] Stakeholder Analysis renders as formatted markdown
- [ ] Malformed markdown falls back to plain text
- [ ] Chat messages container has fixed height
- [ ] Chat auto-scrolls to bottom on new messages
- [ ] Chat input stays at bottom, doesn't get pushed down
- [ ] Version navigation hidden when content is dirty
- [ ] Save/Discard buttons show when content is dirty
- [ ] Version navigation returns after Save or Discard
- [ ] Can switch tabs with unsaved changes (no blocking)
- [ ] Attempting version navigation with unsaved changes shows dialog
- [ ] PDF preview scales to fit container width
- [ ] Fixed footer displays with Back, Skip, Next buttons
- [ ] Skip button navigates to proposals and triggers AI
- [ ] Next button only enabled after saving resume draft
- [ ] Back button navigates to details

### Step 3 - Proposals

- [ ] Title is "Job Intake: Step 3 of 3 - Experience Updates"
- [ ] Subtitle displays
- [ ] Outer card removed from proposals section
- [ ] Individual proposals still in cards
- [ ] Empty state shows "No updates found." centered
- [ ] Button text is "Finish" not "Complete Intake Workflow"
- [ ] Fixed footer displays with Back and Finish buttons
- [ ] Back navigates to experience
- [ ] Finish navigates to job detail page

### Resume Tab

- [ ] Displays same interface as Step 2 Experience
- [ ] Chat history from intake workflow loads
- [ ] All resume versions from intake appear
- [ ] Gap and Stakeholder analyses display
- [ ] No fixed footer navigation (correctly omitted)
- [ ] No "Step X of 3" title (correctly omitted)
- [ ] All editing functionality works
- [ ] Markdown renders properly
- [ ] PDF scales correctly

### Notes Tab

- [ ] Left column is scrollable when notes exceed viewport
- [ ] Right column stays sticky at top
- [ ] Can scroll through many notes while add form stays visible

### General

- [ ] Layout file deleted
- [ ] No progress indicators display
- [ ] All pages have appropriate container widths
- [ ] No console errors
- [ ] Responsive design works on mobile/tablet

## Success Criteria

This sprint will be considered successful when:

1. All navigation buttons are fixed at the bottom of the viewport during the intake workflow
2. All visual progress indicators are removed from the intake flow
3. Gap Analysis and Stakeholder Analysis render as formatted markdown
4. Chat interface maintains fixed height and doesn't push input off-screen
5. Resume Tab provides identical functionality to Step 2 with data continuity from intake
6. All test cases in the Testing Checklist pass
7. No new console errors introduced
8. Responsive design works on mobile and tablet devices

## Assumptions and Dependencies

### Assumptions

- Users have modern browsers that support CSS `calc()` and fixed positioning
- Intake session data structure supports storing chat messages
- Current PDF preview implementation uses `react-pdf` library
- Tailwind typography plugin is available or custom prose classes can be created

### Dependencies

- Must install `react-markdown` and `remark-gfm` packages before implementing Step 2 changes
- API endpoints for chat history management must exist or be created
- shadcn/ui components (Separator, Popover) must be available in the project

### Risks

- Large refactoring of Step 2 into shared component could introduce bugs
- Chat height calculation might need fine-tuning across different screen sizes
- PDF scaling might behave differently across browsers

## Notes for Implementation

- The fixed footer should have a z-index high enough to stay above other content but not block modals
- When extracting the shared component, ensure all state management logic is properly encapsulated
- Test thoroughly on mobile devices as fixed footers can be problematic with virtual keyboards
- Consider adding a data-testid attribute to key elements for easier automated testing
- The `h-[calc(100vh-400px)]` value for chat may need adjustment during implementation; treat it as a starting point
