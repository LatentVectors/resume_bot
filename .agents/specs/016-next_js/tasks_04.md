# Spec Tasks

## Tasks

- [x] 1. Update Step 1 Job Details Form Layout and Fields

  - [x] 1.1 Remove Card wrapper from JobDetailsForm component (keep form content only)
  - [x] 1.2 Add FormLabel components for Job Title, Company Name, and Job Description fields
  - [x] 1.3 Update Job Description textarea className from `min-h-[400px] resize-y` to `h-[250px] resize-none overflow-y-auto`
  - [x] 1.4 Add `delayDuration={500}` prop to TooltipProvider component

- [x] 2. Fix Step 1 Navigation Flow

  - [x] 2.1 Update `handleJobCreated` function in `apps/web/src/app/intake/new/details/page.tsx` to navigate to `/intake/${jobId}/experience` instead of `/intake/${jobId}/details`
  - [x] 2.2 Test that creating a new job skips the redundant details page

- [x] 3. Add Fixed Footer to Step 1 Details Page

  - [x] 3.1 Remove existing navigation buttons from JobDetailsForm (Cancel and Next buttons at bottom of form)
  - [x] 3.2 Add fixed footer to `apps/web/src/app/intake/[jobId]/details/page.tsx` with className `fixed bottom-0 left-0 right-0 bg-background border-t z-50 p-4`
  - [x] 3.3 Add Cancel and Next buttons to the fixed footer
  - [x] 3.4 Add `pb-24` to page content wrapper to prevent content from being hidden behind footer
  - [x] 3.5 Add `max-w-4xl` container wrapper to the page

- [x] 4. Install Required Dependencies

  - [x] 4.1 Run `npm install react-markdown remark-gfm` in apps/web directory
  - [x] 4.2 Verify packages are added to package.json

- [x] 5. Create MarkdownRenderer Utility Component

  - [x] 5.1 Create `apps/web/src/components/intake/MarkdownRenderer.tsx`
  - [x] 5.2 Implement component that wraps react-markdown with remark-gfm plugin
  - [x] 5.3 Add error handling to fall back to plain text if rendering fails
  - [x] 5.4 Apply `prose prose-sm` Tailwind classes for styling
  - [x] 5.5 Export component with props interface for markdown content string

- [x] 6. Create ActionsMenu Utility Component

  - [x] 6.1 Create `apps/web/src/components/intake/ActionsMenu.tsx`
  - [x] 6.2 Implement Popover component with MoreVertical icon trigger button
  - [x] 6.3 Accept array of action items as props (label, onClick, icon)
  - [x] 6.4 Render action buttons in PopoverContent
  - [x] 6.5 Style with ghost button variant

- [x] 7. Create PDFPreview Utility Component

  - [x] 7.1 Create `apps/web/src/components/intake/PDFPreview.tsx`
  - [x] 7.2 Implement PDF viewer using react-pdf Document and Page components
  - [x] 7.3 Add containerRef and useState for dynamic width calculation
  - [x] 7.4 Use useEffect to set width based on container offsetWidth
  - [x] 7.5 Pass width prop to Page component for automatic scaling
  - [x] 7.6 Add loading and error state handling

- [x] 8. Update Step 2 Layout and Width

  - [x] 8.1 Change container in `apps/web/src/app/intake/[jobId]/experience/page.tsx` from `max-w-4xl` to `max-w-6xl`
  - [x] 8.2 Add Separator component with `orientation="vertical"` between the two columns
  - [x] 8.3 Remove card wrapper from right column content
  - [x] 8.4 Verify two-column layout maintains proper spacing

- [x] 9. Implement Actions Menu in Step 2

  - [x] 9.1 Import ActionsMenu component in experience page
  - [x] 9.2 Replace existing copy button with ActionsMenu component
  - [x] 9.3 Pass "Copy Job Context" action with existing handleCopyJobContext function
  - [x] 9.4 Test that copying job context works from the new menu

- [x] 10. Add Markdown Rendering to Gap and Stakeholder Analysis

  - [x] 10.1 Import MarkdownRenderer component in experience page
  - [x] 10.2 Replace plain text rendering of Gap Analysis with MarkdownRenderer
  - [x] 10.3 Replace plain text rendering of Stakeholder Analysis with MarkdownRenderer
  - [x] 10.4 Test with properly formatted markdown content
  - [x] 10.5 Test fallback behavior with malformed markdown

- [x] 11. Fix Chat Interface Scrolling in Step 2

  - [x] 11.1 Locate the chat messages container element in ChatInterface component
  - [x] 11.2 Add `h-[calc(100vh-400px)] overflow-y-auto` classes to messages container
  - [x] 11.3 Ensure chat input remains fixed at bottom of chat area
  - [x] 11.4 Verify auto-scroll to bottom on new messages (or implement if not present)
  - [x] 11.5 Test with varying numbers of messages

- [x] 12. Implement Conditional Save/Discard UI in Step 2

  - [x] 12.1 Add state variable to track if version navigation should be hidden
  - [x] 12.2 Conditionally render version navigation row only when content is NOT dirty
  - [x] 12.3 Conditionally render Save and Discard buttons only when content IS dirty
  - [x] 12.4 Update handleSave to restore version navigation after save
  - [x] 12.5 Update handleDiscard to restore version navigation after discard
  - [x] 12.6 Modify version navigation handlers to check isDirty and show unsaved dialog instead of directly navigating
  - [x] 12.7 Ensure tab switching (Job Context, Gap Analysis, Preview) is NOT blocked by dirty state

- [x] 13. Fix PDF Preview Scaling in Step 2

  - [x] 13.1 Replace current PDF preview implementation with PDFPreview component
  - [x] 13.2 Pass pdfPreviewUrl to PDFPreview component
  - [x] 13.3 Verify PDF scales to fit container width
  - [x] 13.4 Test scrolling through multi-page PDFs

- [x] 14. Add Fixed Footer to Step 2 Experience Page

  - [x] 14.1 Remove existing navigation buttons from the page
  - [x] 14.2 Add fixed footer with className `fixed bottom-0 left-0 right-0 bg-background border-t z-50 p-4`
  - [x] 14.3 Add Back button that navigates to `/intake/{jobId}/details`
  - [x] 14.4 Add Skip button that navigates to `/intake/{jobId}/proposals` and triggers proposal generation
  - [x] 14.5 Add Next button (enabled only when resume draft saved) that navigates to `/intake/{jobId}/proposals`
  - [x] 14.6 Add `pb-24` to page content to prevent content hiding

- [x] 15. Extract ExperienceResumeInterface Shared Component

  - [x] 15.1 Create `apps/web/src/components/intake/ExperienceResumeInterface.tsx`
  - [x] 15.2 Define ExperienceResumeInterfaceProps interface with jobId, showStepTitle, showFooter
  - [x] 15.3 Move all Step 2 experience page logic into this new component
  - [x] 15.4 Include two-column layout, chat interface, tabs, version navigation, resume editing
  - [x] 15.5 Conditionally render step title based on showStepTitle prop
  - [x] 15.6 Conditionally render fixed footer based on showFooter prop

- [x] 16. Refactor Step 2 to Use Shared Component

  - [x] 16.1 Update `apps/web/src/app/intake/[jobId]/experience/page.tsx` to import ExperienceResumeInterface
  - [x] 16.2 Replace existing implementation with ExperienceResumeInterface component
  - [x] 16.3 Pass jobId, showStepTitle={true}, showFooter={true} as props
  - [x] 16.4 Verify all Step 2 functionality still works
  - [x] 16.5 Remove unused code from experience page

- [x] 17. Verify or Create Chat History API Endpoints

  - [x] 17.1 Check if `GET /api/jobs/{job_id}/intake-session/messages` endpoint exists
  - [x] 17.2 Check if `POST /api/jobs/{job_id}/intake-session/messages` endpoint exists
  - [x] 17.3 If endpoints don't exist, create them in `apps/api/api/routes/jobs.py`
  - [x] 17.4 Ensure endpoints properly store and retrieve chat message history
  - [x] 17.5 Test endpoints with sample data

- [x] 18. Update Resume Tab to Use Shared Component

  - [x] 18.1 Update `apps/web/src/components/job-detail/ResumeTab.tsx` to import ExperienceResumeInterface
  - [x] 18.2 Replace existing implementation with ExperienceResumeInterface component
  - [x] 18.3 Pass jobId, showStepTitle={false}, showFooter={false} as props
  - [x] 18.4 Add data fetching for chat history using intake session messages endpoint
  - [x] 18.5 Ensure all resume versions from intake session are accessible
  - [x] 18.6 Verify gap analysis and stakeholder analysis display correctly
  - [x] 18.7 Test that no fixed footer or step title appears on Resume Tab

- [x] 19. Update Step 3 Title and Layout

  - [x] 19.1 Update title in `apps/web/src/app/intake/[jobId]/proposals/page.tsx` to "Job Intake: Step 3 of 3 - Experience Updates"
  - [x] 19.2 Add subtitle describing the purpose below the title
  - [x] 19.3 Remove Card wrapper around entire "Experience Proposals" section
  - [x] 19.4 Keep section title directly on page (not in card)
  - [x] 19.5 Verify individual proposal cards remain as Card components

- [x] 20. Update Step 3 Empty State and Button

  - [x] 20.1 Update empty state to display centered message "No updates found."
  - [x] 20.2 Change "Complete Intake Workflow" button text to "Finish"
  - [x] 20.3 Verify button still navigates to job detail page

- [x] 21. Add Fixed Footer to Step 3 Proposals Page

  - [x] 21.1 Remove existing "Complete Intake Workflow" / "Finish" button from page content
  - [x] 21.2 Add fixed footer with className `fixed bottom-0 left-0 right-0 bg-background border-t z-50 p-4`
  - [x] 21.3 Add Back button that navigates to `/intake/{jobId}/experience`
  - [x] 21.4 Add Finish button that navigates to `/jobs/{jobId}` and marks intake complete
  - [x] 21.5 Add `pb-24` to page content wrapper
  - [x] 21.6 Add `max-w-4xl` container wrapper to the page

- [x] 22. Update Notes Tab Scrolling Behavior

  - [x] 22.1 Add `max-h-[calc(100vh-200px)] overflow-y-auto` to left column in `apps/web/src/components/job-detail/NotesTab.tsx`
  - [x] 22.2 Verify right column sticky positioning still works with `lg:sticky lg:top-20`
  - [x] 22.3 Test with many notes to ensure scrolling works correctly
  - [x] 22.4 Verify add note form stays accessible
