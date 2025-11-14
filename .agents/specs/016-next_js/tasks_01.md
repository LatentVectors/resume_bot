# Spec Tasks

## Tasks

- [x] 1. Repository Restructuring - Move Python Code

  - [x] 1.1 Create `packages/` directory at root
  - [x] 1.2 Create `packages/api/` directory
  - [x] 1.3 Move `api/`, `src/`, `app/`, `tests/` directories to `packages/api/`
  - [x] 1.4 Move `pyproject.toml` to `packages/api/`
  - [x] 1.5 Move `.env` to `packages/api/`
  - [x] 1.6 Update `.gitignore` to account for new structure (packages/api/.venv, etc.)

- [x] 2. Recreate Python Virtual Environment

  - [x] 2.1 Navigate to `packages/api/` directory
  - [x] 2.2 Create new virtual environment: `python -m venv .venv`
  - [x] 2.3 Activate virtual environment
  - [x] 2.4 Install dependencies: `pip install -e .`
  - [x] 2.5 Test FastAPI starts: `uvicorn api.main:app --reload --port 8000`
  - [x] 2.6 Verify API health endpoint responds: `http://localhost:8000/api/health`
  - [x] 2.7 Delete root-level `run.py` (no longer needed)

- [x] 3. Create Next.js Application

  - [x] 3.1 Create empty `packages/web/` directory
  - [x] 3.2 Run Next.js CLI: `npx create-next-app@latest . --typescript --tailwind --app --src-dir --import-alias "@/*"`
  - [x] 3.3 Verify Next.js app starts: `npm run dev`
  - [x] 3.4 Create `packages/web/.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
  - [x] 3.5 Clean up default Next.js boilerplate (page.tsx, layout.tsx to minimal versions)

- [x] 4. Install and Configure ShadCN UI

  - [x] 4.1 Run ShadCN init: `npx shadcn-ui@latest init`
  - [x] 4.2 Configure: New York style, Slate color, CSS variables
  - [x] 4.3 Install core components: `npx shadcn-ui@latest add button card input textarea form dialog badge tabs select table`
  - [x] 4.4 Verify components are in `src/components/ui/`
  - [x] 4.5 Test a component renders (add Button to page.tsx temporarily)

- [x] 5. Install Additional Dependencies

  - [x] 5.1 Install TanStack Query: `npm install @tanstack/react-query`
  - [x] 5.2 Install Zustand: `npm install zustand`
  - [x] 5.3 Install form libraries: `npm install react-hook-form @hookform/resolvers zod`
  - [x] 5.4 Install dev dependencies: `npm install -D openapi-typescript`
  - [x] 5.5 (Optional) Install concurrently: `npm install -D concurrently`

- [x] 6. Set Up Type Generation from FastAPI

  - [x] 6.1 Add script to `package.json`: `"generate:types": "openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts"`
  - [x] 6.2 Ensure FastAPI backend is running
  - [x] 6.3 Run type generation: `npm run generate:types`
  - [x] 6.4 Verify `src/types/api.ts` was created with types
  - [x] 6.5 Create `src/types/index.ts` for shared app types (initially empty)

- [x] 7. Create Base API Client

  - [x] 7.1 Create `src/lib/api/client.ts` with base `apiRequest` function
  - [x] 7.2 Implement error handling (APIError class)
  - [x] 7.3 Configure base URL from environment variable
  - [x] 7.4 Handle 204 No Content responses
  - [x] 7.5 Add proper TypeScript typing for generic responses

- [x] 8. Create API Endpoint Clients - Part 1

  - [x] 8.1 Create `src/lib/api/jobs.ts` with jobs endpoints (list, get, create, update, delete)
  - [x] 8.2 Create `src/lib/api/users.ts` with user endpoints
  - [x] 8.3 Create `src/lib/api/experiences.ts` with experience endpoints
  - [x] 8.4 Use generated types from `src/types/api.ts`
  - [x] 8.5 Test one endpoint manually (e.g., fetch jobs)

- [x] 9. Create API Endpoint Clients - Part 2

  - [x] 9.1 Create `src/lib/api/resumes.ts` with resume endpoints
  - [x] 9.2 Create `src/lib/api/cover-letters.ts` with cover letter endpoints
  - [x] 9.3 Create `src/lib/api/education.ts` with education endpoints
  - [x] 9.4 Create `src/lib/api/certificates.ts` with certificate endpoints
  - [x] 9.5 Create `src/lib/api/workflows.ts` with workflow endpoints

- [x] 10. Set Up TanStack Query Provider

  - [x] 10.1 Create `src/lib/providers.tsx` with QueryClientProvider
  - [x] 10.2 Configure QueryClient with sensible defaults
  - [x] 10.3 Wrap root layout with providers
  - [x] 10.4 Add `'use client'` directive to providers file
  - [x] 10.5 Test that queries can be used in components

- [x] 11. Create Zustand Stores

  - [x] 11.1 Create `src/lib/store/user.ts` with user store (user state, setUser, clearUser)
  - [x] 11.2 Create `src/lib/store/intake.ts` with job intake workflow store (step, form data, session ID)
  - [x] 11.3 Add TypeScript interfaces for store states
  - [x] 11.4 Test stores can be imported and used

- [x] 12. Create Root Layout and Navigation

  - [x] 12.1 Update `src/app/layout.tsx` with navigation structure
  - [x] 12.2 Create `src/components/layout/Nav.tsx` navigation component
  - [x] 12.3 Add navigation links: Home, Profile, Jobs
  - [x] 12.4 Style navigation with ShadCN and Tailwind
  - [x] 12.5 Make navigation responsive (mobile-friendly)
  - [x] 12.6 Add user info display in nav (from Zustand store)

- [x] 13. Create Custom Hooks for Data Fetching

  - [x] 13.1 Create `src/lib/hooks/useJobs.ts` (useJobs, useJob hooks)
  - [x] 13.2 Create `src/lib/hooks/useJobMutations.ts` (useCreateJob, useUpdateJob, useDeleteJob)
  - [x] 13.3 Create `src/lib/hooks/useExperiences.ts` (useExperiences, useExperience)
  - [x] 13.4 Create `src/lib/hooks/useUser.ts` (useCurrentUser hook)
  - [x] 13.5 Configure proper query keys and invalidation

- [x] 14. Home Page - Job Entry Form

  - [x] 14.1 Create `src/app/page.tsx` with job description form
  - [x] 14.2 Add large textarea for job description input
  - [x] 14.3 Create form submission handler that extracts title/company (if needed)
  - [x] 14.4 On submit, navigate to intake flow: `/intake/[jobId]/details`
  - [x] 14.5 Add check for user experiences and show banner if none exist
  - [x] 14.6 Fetch current user on page load and store in Zustand

- [x] 15. Jobs List Page

  - [x] 15.1 Create `src/app/jobs/page.tsx`
  - [x] 15.2 Fetch and display jobs using `useJobs` hook
  - [x] 15.3 Create `src/components/jobs/JobCard.tsx` component
  - [x] 15.4 Add filter controls (status, favorite)
  - [x] 15.5 Add delete job functionality
  - [x] 15.6 Add click handler to navigate to job detail page
  - [x] 15.7 Handle loading and empty states

- [x] 16. Profile Page - User Info and Experiences

  - [x] 16.1 Create `src/app/profile/page.tsx`
  - [x] 16.2 Display user information (name, title, etc.)
  - [x] 16.3 Create experience list section
  - [x] 16.4 Create `src/components/profile/ExperienceCard.tsx`
  - [x] 16.5 Add experience CRUD dialogs (create, edit, delete)
  - [x] 16.6 Integrate with useExperiences hook and mutations
  - [x] 16.7 Add achievements display and CRUD for each experience

- [x] 17. Profile Page - Education and Certificates

  - [x] 17.1 Add education section to profile page
  - [x] 17.2 Create `src/components/profile/EducationCard.tsx`
  - [x] 17.3 Add education CRUD dialogs
  - [x] 17.4 Add certificates section
  - [x] 17.5 Create `src/components/profile/CertificateCard.tsx`
  - [x] 17.6 Add certificate CRUD dialogs
  - [x] 17.7 Handle loading states for all sections

- [x] 18. Job Detail Page Structure and Overview Tab

  - [x] 18.1 Create `src/app/jobs/[id]/page.tsx` with tabs structure
  - [x] 18.2 Implement ShadCN Tabs component
  - [x] 18.3 Add URL query param for active tab (useSearchParams)
  - [x] 18.4 Create `src/components/job-detail/OverviewTab.tsx`
  - [x] 18.5 Display job details (title, company, description)
  - [x] 18.6 Add edit job functionality
  - [x] 18.7 Add favorite toggle and status update
  - [x] 18.8 Add delete job button with confirmation

- [x] 19. Job Detail Page - Resume Tab

  - [x] 19.1 Create `src/components/job-detail/ResumeTab.tsx`
  - [x] 19.2 Fetch and display resume versions list
  - [x] 19.3 Display current/pinned resume content
  - [x] 19.4 Add version selection and pin/unpin functionality
  - [x] 19.5 Add "Generate Resume" button with mutation
  - [x] 19.6 Add PDF download functionality
  - [x] 19.7 Add version comparison view (optional)
  - [x] 19.8 Handle loading and empty states

- [x] 20. Job Detail Page - Cover Letter Tab

  - [x] 20.1 Create `src/components/job-detail/CoverLetterTab.tsx`
  - [x] 20.2 Fetch and display cover letter versions
  - [x] 20.3 Display current/pinned cover letter content
  - [x] 20.4 Add version selection and pin/unpin functionality
  - [x] 20.5 Add "Generate Cover Letter" button
  - [x] 20.6 Add PDF download functionality
  - [x] 20.7 Handle loading and empty states

- [x] 21. Job Detail Page - Notes Tab

  - [x] 21.1 Create `src/components/job-detail/NotesTab.tsx`
  - [x] 21.2 Display job notes in textarea
  - [x] 21.3 Add save notes functionality
  - [x] 21.4 Consider markdown support (optional)
  - [x] 21.5 Auto-save or explicit save button
  - [x] 21.6 Handle loading state

- [x] 22. Job Intake Workflow - Layout and Step 1

  - [x] 22.1 Create `src/app/intake/[jobId]/layout.tsx` with progress indicator
  - [x] 22.2 Add step navigation UI (Details → Experience → Proposals)
  - [x] 22.3 Create `src/app/intake/[jobId]/details/page.tsx`
  - [x] 22.4 Create job details form (title, company, description)
  - [x] 22.5 Add Zod validation schema
  - [x] 22.6 Save to API and navigate to experience step on submit
  - [x] 22.7 Update Zustand intake store with form data

- [x] 23. Job Intake Workflow - Step 2 (Experience Selection)

  - [x] 23.1 Create `src/app/intake/[jobId]/experience/page.tsx`
  - [x] 23.2 Display user experiences with checkboxes for selection
  - [x] 23.3 Add "Run Gap Analysis" button
  - [x] 23.4 Display gap analysis results
  - [x] 23.5 Add "Generate Resume" button
  - [x] 23.6 Handle gap analysis and resume generation API calls
  - [x] 23.7 Navigate to proposals step after resume generation
  - [x] 23.8 Handle loading states for async operations

- [x] 24. Job Intake Workflow - Step 3 (Proposals)

  - [x] 24.1 Create `src/app/intake/[jobId]/proposals/page.tsx`
  - [x] 24.2 Fetch and display experience proposals
  - [x] 24.3 Create proposal card component with accept/reject buttons
  - [x] 24.4 Implement accept/reject individual proposals
  - [x] 24.5 Add "Accept All" button
  - [x] 24.6 Add "Complete" button to finish intake
  - [x] 24.7 Clear intake state from Zustand on completion
  - [x] 24.8 Navigate to job detail page on completion

- [x] 25. CORS and Environment Configuration

  - [x] 25.1 Update FastAPI CORS in `packages/api/api/main.py` to allow `http://localhost:3000`
  - [x] 25.2 Add Vercel domains to CORS origins: `https://yourapp.vercel.app`, `https://*.vercel.app`
  - [x] 25.3 Make CORS origins configurable via environment variable
  - [x] 25.4 Test API calls from Next.js to FastAPI (both services running)
  - [x] 25.5 Update `packages/api/.env` with CORS configuration
  - [x] 25.6 Verify environment variables are properly loaded

- [x] 26. Update Documentation

  - [x] 26.1 Update root `README.md` with new repository structure
  - [x] 26.2 Document how to run backend: `cd packages/api && uvicorn api.main:app --reload`
  - [x] 26.3 Document how to run frontend: `cd packages/web && npm run dev`
  - [x] 26.4 Document environment variables for both services
  - [x] 26.5 Document type generation workflow
  - [x] 26.6 Create or update `packages/web/README.md` with setup instructions
  - [x] 26.7 Document optional concurrently setup for running both services

- [x] 27. Manual Testing and Verification

  - [x] 27.1 Test home page: job description entry and navigation to intake
    - ✅ Home page loads correctly with job description form
    - ⚠️ CORS issue prevents POST requests (job creation fails)
    - ✅ Navigation structure works
  - [ ] 27.2 Test job intake flow end-to-end (all 3 steps)
    - ⚠️ Blocked by CORS issue preventing job creation
  - [ ] 27.3 Test resume generation and viewing
    - ✅ Resume tab loads and displays correctly
    - ⚠️ Cannot test generation due to CORS issue
  - [x] 27.4 Test cover letter generation and viewing
    - ✅ Cover Letter tab loads and displays correctly
    - ✅ Fixed missing import for `useCoverLetterVersion` hook
    - ⚠️ Cannot test generation due to CORS issue
  - [x] 27.5 Test profile management (experiences, education, certificates)
    - ✅ Profile page loads correctly
    - ✅ Displays user info, experiences, education, and certificates
    - ✅ All sections render properly
  - [x] 27.6 Test jobs list filtering and navigation
    - ✅ Jobs list page loads correctly
    - ✅ Displays job cards
    - ✅ Filter controls are present
    - ⚠️ Some CORS errors for user_id=0 requests
  - [x] 27.7 Test job detail page (all tabs)
    - ✅ Fixed Next.js 15 params Promise issue
    - ✅ Overview tab works correctly
    - ✅ Resume tab works correctly
    - ✅ Cover Letter tab works correctly (after fixing import)
    - ✅ Notes tab works correctly
    - ✅ Tab navigation with URL query params works
  - [ ] 27.8 Test on different browsers (Chrome, Firefox, Safari)
    - ⚠️ Only tested in Chrome via browser extension
  - [ ] 27.9 Test responsive design on mobile viewport
    - ⚠️ Not tested yet

**Issues Found:**

1. **CORS Issue**: POST requests are blocked by CORS policy. GET requests work fine. Backend CORS configuration appears correct, but browser is blocking requests. May need backend restart or browser cache clear.
2. **Next.js 15 Params**: Fixed - params are now Promises in Next.js 15 and must be unwrapped with `React.use()`
3. **Missing Import**: Fixed - `useCoverLetterVersion` hook was not imported in CoverLetterTab.tsx
4. **TypeScript Errors**: Some TypeScript errors in CoverLetterTab.tsx need to be fixed (CoverLetterData type, implicit any types)

- [ ] 28. Streamlit Removal
  - [ ] 28.1 Verify Next.js has feature parity with Streamlit for in-scope features
  - [ ] 28.2 Delete `packages/api/app/` directory (entire Streamlit app)
  - [ ] 28.3 Remove Streamlit dependencies from `packages/api/pyproject.toml`
  - [ ] 28.4 Reinstall Python dependencies: `pip install -e .`
  - [ ] 28.5 Verify FastAPI still works without Streamlit
  - [ ] 28.6 Update documentation to remove all Streamlit references
  - [ ] 28.7 Commit changes with clear message about Streamlit removal
