# Next.js Frontend Migration Spec

## Overview

This sprint focuses on migrating the Streamlit frontend to a modern Next.js application with React, TypeScript, and ShadCN UI. In the previous sprint, we refactored the backend to use FastAPI, creating a clean separation between frontend and backend. This sprint completes the architectural migration by replacing Streamlit with a scalable, modern web application.

The goal is not to copy Streamlit exactly, but to port all functionality, UI, and workflows while improving scalability and extensibility. Once the Next.js app is feature-complete and verified working, the Streamlit app will be deleted entirely.

## Problem Statement

The current Streamlit frontend has reached its limitations:

- Difficult to add complex functionality
- Limited UI/UX customization options
- Not designed for modern web application patterns
- Restrictive state management model
- Not suitable for future features (browser extension integration, advanced workflows)

## Scope

### In Scope for This Sprint

**Pages to Implement:**

- Home page (job description entry form)
- User profile page
- Jobs list page
- Job detail page with tabs
- Job intake workflow (multi-step)

**Job Detail Page Tabs:**

- Overview tab
- Resume tab
- Cover Letter tab
- Notes tab

**Excluded from This Sprint:**

- Templates page (defer to future sprint)
- Responses page (defer to future sprint)
- Messages tab on job detail page (defer to future sprint)
- Responses tab on job detail page (defer to future sprint)
- Testing infrastructure (defer to future sprint)

### Future Considerations

This restructuring prepares the repository for future services:

- Browser extension (future sprint, directory reserved as `browser-extension/`)
- Additional microservices as needed
- Multi-user authentication via Supabase Auth (future sprint)

## Repository Restructuring

To support multiple services (web frontend, API backend, future browser extension) without cluttering the repository root, we will reorganize the project structure.

### Current Structure

```
resume/
├── api/              # FastAPI backend
├── src/              # Shared Python code
├── app/              # Streamlit frontend
├── tests/            # Python tests
├── pyproject.toml
└── run.py
```

### Target Structure

```
resume/
├── packages/
│   ├── api/              # All Python/FastAPI code
│   │   ├── api/          # Current api/ contents (routes, schemas, services)
│   │   ├── src/          # Current src/ contents (agents, core, features)
│   │   ├── app/          # Current app/ contents (Streamlit - delete after migration)
│   │   ├── tests/        # Python tests
│   │   ├── pyproject.toml # Moved from root
│   │   ├── .env          # Backend environment variables
│   │   └── run_api.py    # Run FastAPI only
│   └── web/              # Next.js frontend (new)
│       ├── src/
│       │   ├── app/           # Next.js App Router pages
│       │   ├── components/    # React components
│       │   ├── lib/           # Utilities, API client, config
│       │   └── types/         # TypeScript types
│       ├── public/
│       ├── package.json
│       ├── next.config.js
│       ├── tailwind.config.ts
│       ├── tsconfig.json
│       └── .env.local
├── .agents/          # Development specs (keep at root)
├── __notes__/        # Development notes (keep at root)
├── .gitignore
└── README.md         # Updated with new structure
```

### Python Environment & Execution

**Virtual Environment:**

- Create and activate virtual environment in `packages/api/` directory
- Run all Python commands from `packages/api/` directory
- No changes to imports needed - they remain as-is: `from api.schemas.job import JobResponse`

**Key Point:** By running commands from `packages/api/` directory, all imports work without modification. No Python path manipulation or sys.path changes needed.

## Technology Stack

### Frontend (Next.js)

**Core Framework:**

- Next.js 14+ (latest version)
- React 18+
- TypeScript 5+

**UI Framework:**

- ShadCN UI with "New York" style
- Slate color scheme
- Tailwind CSS for styling

**State Management & Data Fetching:**

- TanStack Query (React Query) - server state, caching, API calls
- Zustand - client state management (UI state, complex workflows)
- React Hook Form - form handling
- Zod - schema validation

**Type Safety:**

- openapi-typescript - generate TypeScript types from FastAPI OpenAPI schema

**Routing:**

- Next.js App Router (file-based routing)
- Custom import alias (`@/`)

**Development Tools:**

- ESLint for linting
- TypeScript for type checking

### Backend (Existing)

- FastAPI (Python)
- SQLite database (current)
- OpenAI/LangChain for LLM workflows

## Next.js Configuration

### CLI Setup

Create Next.js app using the CLI in an empty directory:

```bash
# Create empty web directory first
mkdir -p packages/web
cd packages/web

# Run Next.js creation CLI
npx create-next-app@latest . --typescript --tailwind --app --src-dir --import-alias "@/*"
```

**CLI Selections:**

- TypeScript: Yes
- ESLint: Yes
- Tailwind CSS: Yes
- `src/` directory: Yes
- App Router: Yes
- Customize default import alias: Yes, use `@/*`

### ShadCN UI Setup

After Next.js creation, set up ShadCN:

```bash
cd packages/web
npx shadcn-ui@latest init
```

**Configuration:**

- Style: New York (minimal, clean)
- Base color: Slate
- CSS variables: Yes

**Initial Components to Install:**

```bash
npx shadcn-ui@latest add button card input textarea form dialog badge tabs select table
```

### Additional Dependencies

Install additional required packages:

```bash
npm install @tanstack/react-query zustand react-hook-form @hookform/resolvers zod
npm install -D openapi-typescript
```

## Type Generation from FastAPI

### Strategy

Use `openapi-typescript` to automatically generate TypeScript types from FastAPI's OpenAPI specification.

### Implementation

1. **Add npm script** to `packages/web/package.json`:

```json
{
  "scripts": {
    "generate:types": "openapi-typescript http://localhost:8000/openapi.json -o src/types/api.ts"
  }
}
```

2. **Generation workflow:**

   - Ensure FastAPI backend is running on port 8000
   - Run `npm run generate:types` to fetch OpenAPI spec and generate types
   - Generated types will be in `packages/web/src/types/api.ts`
   - Import and use types throughout the frontend

3. **Keep types in sync:**
   - Regenerate types after any API schema changes
   - Consider adding type generation to development workflow
   - Document in README when to regenerate types

## Application Architecture

### Route Structure

Using Next.js App Router with file-based routing:

```
packages/web/src/app/
├── layout.tsx                    # Root layout with nav, providers
├── page.tsx                      # Home page (job entry form)
├── profile/
│   └── page.tsx                  # User profile page
├── jobs/
│   ├── page.tsx                  # Jobs list page
│   └── [id]/
│       └── page.tsx              # Job detail page with tabs
└── intake/
    └── [jobId]/
        ├── layout.tsx            # Intake flow layout with progress indicator
        ├── details/
        │   └── page.tsx          # Step 1: Job details
        ├── experience/
        │   └── page.tsx          # Step 2: Experience selection & resume generation
        └── proposals/
            └── page.tsx          # Step 3: Experience proposals review
```

**URLs:**

- `/` - Home page
- `/profile` - User profile
- `/jobs` - Jobs list
- `/jobs/123` - Job detail
- `/intake/123/details` - Job intake step 1
- `/intake/123/experience` - Job intake step 2
- `/intake/123/proposals` - Job intake step 3

### Job Intake Workflow

The job intake workflow will be implemented as **dedicated routes** rather than a modal dialog.

**Rationale:**

- Each step has its own URL for bookmarking and navigation
- Browser back/forward buttons work naturally
- Better for complex, multi-step workflows
- Clearer step progression with dedicated layouts
- Can track analytics per step
- Users can return to incomplete workflows via URL

**Implementation Details:**

- Create `packages/web/src/app/intake/[jobId]/layout.tsx` with:
  - Progress indicator showing current step (1/3, 2/3, 3/3)
  - Step names: Details → Experience → Proposals
  - Navigation guard to prevent skipping steps
- Each step is a separate page component
- Use Zustand to manage workflow state across steps
- Persist session data to API after each step completion
- On incomplete sessions, redirect users to the correct step URL

**Step Components:**

1. **Details** (`/intake/[jobId]/details`): Job title, company, description form
2. **Experience** (`/intake/[jobId]/experience`): Experience selection, gap analysis, resume generation
3. **Proposals** (`/intake/[jobId]/proposals`): Review and accept/reject experience proposals

### Job Detail Page

Implement tabs using ShadCN Tabs component:

```typescript
// packages/web/src/app/jobs/[id]/page.tsx
<Tabs defaultValue="overview" value={tab} onValueChange={setTab}>
  <TabsList>
    <TabsTrigger value="overview">Overview</TabsTrigger>
    <TabsTrigger value="resume">Resume</TabsTrigger>
    <TabsTrigger value="cover">Cover Letter</TabsTrigger>
    <TabsTrigger value="notes">Notes</TabsTrigger>
  </TabsList>
  <TabsContent value="overview">...</TabsContent>
  <TabsContent value="resume">...</TabsContent>
  <TabsContent value="cover">...</TabsContent>
  <TabsContent value="notes">...</TabsContent>
</Tabs>
```

**Tab State Management:**

- Use URL query parameter for active tab: `/jobs/123?tab=resume`
- Enables direct linking to specific tabs
- Preserves tab selection on page refresh
- Use Next.js router to update query param on tab change

**Tab Components Location:**

- Create reusable tab components in `packages/web/src/components/job-detail/`
- Each tab is a separate component: `OverviewTab.tsx`, `ResumeTab.tsx`, etc.

### API Client Implementation

Create a typed API client using fetch and TanStack Query.

**Base Client:**

```typescript
// packages/web/src/lib/api/client.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return response.json();
}
```

**Endpoint-Specific Clients:**

```typescript
// packages/web/src/lib/api/jobs.ts
import { apiRequest } from "./client";
import type { components } from "@/types/api"; // Generated types

type JobResponse = components["schemas"]["JobResponse"];
type JobCreate = components["schemas"]["JobCreate"];

export const jobsAPI = {
  list: (userId: number) =>
    apiRequest<JobResponse[]>(`/api/v1/jobs?user_id=${userId}`),

  get: (id: number) => apiRequest<JobResponse>(`/api/v1/jobs/${id}`),

  create: (data: JobCreate) =>
    apiRequest<JobResponse>("/api/v1/jobs", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
```

**TanStack Query Integration:**

```typescript
// In components
import { useQuery, useMutation } from "@tanstack/react-query";
import { jobsAPI } from "@/lib/api/jobs";

function JobsList() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["jobs", userId],
    queryFn: () => jobsAPI.list(userId),
  });

  const createJob = useMutation({
    mutationFn: jobsAPI.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}
```

### State Management Strategy

**Server State (TanStack Query):**

- All API data: jobs, experiences, resumes, cover letters
- Automatic caching, refetching, and synchronization
- Optimistic updates for mutations
- Background refetching when data is stale

**Client State (Zustand):**

- Current user information
- Job intake workflow state (current step, form data)
- UI state (modals open/closed, sidebar state)
- Theme preferences

**Form State (React Hook Form):**

- All form inputs and validation
- Integrated with Zod schemas for validation
- Used with ShadCN form components

### Data Fetching Pattern

Use **client components with TanStack Query** for all data fetching:

- All page components marked with `'use client'`
- Use TanStack Query hooks for API calls
- Consistent pattern across all pages
- Simple mental model, good for authenticated SPAs
- Not using Next.js server components for this app (all data is user-specific)

## Environment Configuration

### Backend Environment Variables

Update `packages/api/.env`:

```bash
# Existing variables
OPENROUTER_API_KEY=...
LANGCHAIN_API_KEY=...
DATABASE_URL=sqlite:///...

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true

# CORS Origins
CORS_ORIGINS=http://localhost:3000,https://yourapp.vercel.app,https://*.vercel.app
```

### Frontend Environment Variables

Create `packages/web/.env.local`:

```bash
# API Backend URL
NEXT_PUBLIC_API_URL=http://localhost:8000

# Future: Additional config
# NEXT_PUBLIC_APP_NAME=Resume Bot
```

**Environment-Specific Configuration:**

- **Development:** `NEXT_PUBLIC_API_URL=http://localhost:8000`
- **Production (Vercel):** `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`
- Configure in Vercel dashboard or `.env.production`

## CORS Configuration

Update FastAPI CORS configuration to support Vercel deployments:

```python
# packages/api/api/main.py
from fastapi.middleware.cors import CORSMiddleware

origins = [
    "http://localhost:3000",           # Local Next.js dev
    "https://yourapp.vercel.app",      # Production Next.js
    "https://*.vercel.app",            # Vercel preview deployments
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Make origins configurable via environment variable for flexibility.

## Development Workflow

### Running the Application

Each service runs independently from its own directory. No root-level orchestration script needed.

**Running Backend (FastAPI):**

```bash
cd packages/api
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uvicorn api.main:app --reload --port 8000
```

**Running Frontend (Next.js):**

```bash
cd packages/web
npm run dev
```

**Automatic Backend Startup from Frontend (Optional):**

Add a script to `packages/web/package.json` to automatically start the backend when starting the dev server:

```json
{
  "scripts": {
    "dev": "next dev",
    "dev:all": "concurrently \"npm run dev\" \"npm run dev:api\"",
    "dev:api": "cd ../api && source .venv/bin/activate && uvicorn api.main:app --reload --port 8000"
  }
}
```

Install `concurrently` if using the combined script:

```bash
npm install -D concurrently
```

Then run both services with:

```bash
cd packages/web
npm run dev:all
```

**Recommendation:** Start with running services independently in separate terminals for simplicity. Add the combined script later if needed. Future: Consider NX or Turbo for monorepo tooling.

## Authentication & User Management

### Current Sprint: Single User Model

Maintain the current single-user authentication model:

- Continue using `UsersAPI.get_current_user()` pattern
- Store current user in Zustand store after initial fetch
- No login/logout functionality
- No session management needed

### Implementation:

```typescript
// packages/web/src/lib/store/user.ts
import { create } from "zustand";

interface UserStore {
  user: User | null;
  setUser: (user: User | null) => void;
}

export const useUserStore = create<UserStore>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));
```

Fetch user on app initialization and store in Zustand.

### Future: Supabase Auth

The architecture is designed to easily add Supabase authentication later:

- Replace single user store with proper auth session
- Add login/logout pages
- Update API client to include auth tokens
- No changes to component structure needed

## Deployment Strategy

### Frontend (Vercel)

- Deploy Next.js app to Vercel
- Connect GitHub repository
- Configure environment variables in Vercel dashboard
- Automatic deployments on push to main
- Preview deployments for PRs

### Backend (LsngServ or similar)

- Deploy FastAPI to LangServ, AWS Lambda, or similar service
- Must support long-running agent workflows
- Configure CORS to allow Vercel domain
- Set environment variables for API keys
- Update `NEXT_PUBLIC_API_URL` in Vercel to point to deployed API

**Note:** FastAPI could be deployed to Vercel if needed, but serverless functions may have timeout limitations for long-running agent workflows.

## Streamlit Deprecation Strategy

### During Development

- Keep Streamlit app functional without modifications
- Use as reference while building Next.js features
- Do not make any updates or improvements to Streamlit
- Minimize effort spent on Streamlit maintenance

### After Migration

Once Next.js is feature-complete and verified:

1. Test all workflows in Next.js
2. Verify API integration works correctly
3. Delete `packages/api/app/` directory entirely
4. Remove Streamlit dependencies from `pyproject.toml`:
   - `streamlit`
   - `streamlit[pdf]`
   - Any Streamlit-specific packages
5. Remove Streamlit imports from any remaining files
6. Update documentation to remove Streamlit references

**No parallel operation needed:** Once Next.js works, delete Streamlit immediately. YOU MUST CONFIRM WITH THE USER BEFORE DELETING! DO THIS AT THE VERY END.

## Implementation Checklist

### Phase 1: Repository Restructuring

- [ ] Create `packages/` directory
- [ ] Move Python code to `packages/api/`
  - [ ] Move `api/`, `src/`, `app/`, `tests/` directories
  - [ ] Move `pyproject.toml` to `packages/api/`
  - [ ] Move `.env` to `packages/api/`
- [ ] Recreate virtual environment in `packages/api/`:
  - [ ] `cd packages/api`
  - [ ] `python -m venv .venv`
  - [ ] Activate and reinstall dependencies: `pip install -e .`
- [ ] Test that FastAPI still works from `packages/api/` directory
- [ ] Delete root-level `run.py` (no longer needed)
- [ ] Update `.gitignore` for new structure
- [ ] Update README with new run instructions

### Phase 2: Next.js Setup

- [ ] Create empty `packages/web/` directory
- [ ] Run `npx create-next-app@latest` with TypeScript, Tailwind, App Router
- [ ] Initialize ShadCN UI with New York style, Slate theme
- [ ] Install ShadCN components: button, card, input, textarea, form, dialog, badge, tabs, select, table
- [ ] Install dependencies: TanStack Query, Zustand, React Hook Form, Zod
- [ ] Install dev dependencies: openapi-typescript
- [ ] Configure `next.config.js` if needed
- [ ] Set up `packages/web/.env.local` with API URL
- [ ] (Optional) Add `concurrently` script to start both services
- [ ] Create or update README in `packages/web/` with setup instructions

### Phase 3: Type Generation & API Client

- [ ] Add type generation script to `package.json`
- [ ] Generate TypeScript types from FastAPI OpenAPI spec
- [ ] Create base API client in `packages/web/src/lib/api/client.ts`
- [ ] Create endpoint-specific clients:
  - [ ] `jobs.ts`
  - [ ] `experiences.ts`
  - [ ] `users.ts`
  - [ ] `resumes.ts`
  - [ ] `cover-letters.ts`
  - [ ] `workflows.ts`
- [ ] Set up TanStack Query provider in root layout
- [ ] Create Zustand stores for user and workflow state

### Phase 4: Layout & Navigation

- [ ] Create root layout with navigation bar
- [ ] Add navigation links: Home, Profile, Jobs
- [ ] Style navigation with ShadCN components
- [ ] Create responsive layout (mobile-friendly)
- [ ] Add footer if needed

### Phase 5: Core Pages

- [ ] **Home Page** (`packages/web/src/app/page.tsx`)
  - [ ] Job description textarea
  - [ ] Extract title/company on form submission
  - [ ] Navigate to intake flow after submission
- [ ] **Profile Page** (`packages/web/src/app/profile/page.tsx`)

  - [ ] Display user information
  - [ ] List experiences with CRUD operations
  - [ ] List education with CRUD operations
  - [ ] List certificates with CRUD operations
  - [ ] Forms for adding/editing profile data

- [ ] **Jobs List Page** (`packages/web/src/app/jobs/page.tsx`)
  - [ ] Display jobs in cards or table
  - [ ] Filter by status (Saved, Applied, etc.)
  - [ ] Filter by favorite
  - [ ] Navigate to job detail on click
  - [ ] Delete job functionality

### Phase 6: Job Detail Page

- [ ] Create job detail page with tabs (`packages/web/src/app/jobs/[id]/page.tsx`)
- [ ] Implement tab navigation with URL query params
- [ ] **Overview Tab**
  - [ ] Display job details (title, company, description)
  - [ ] Edit job information
  - [ ] Favorite toggle
  - [ ] Status update
  - [ ] Delete job
- [ ] **Resume Tab**
  - [ ] List resume versions
  - [ ] Display current resume content
  - [ ] Pin/unpin versions
  - [ ] Generate new resume version
  - [ ] Download PDF
  - [ ] Compare versions
- [ ] **Cover Letter Tab**
  - [ ] List cover letter versions
  - [ ] Display current cover letter content
  - [ ] Pin/unpin versions
  - [ ] Generate new cover letter
  - [ ] Download PDF
- [ ] **Notes Tab**
  - [ ] Display job notes
  - [ ] Edit notes (markdown editor)
  - [ ] Save notes

### Phase 7: Job Intake Workflow

- [ ] Create intake layout with progress indicator (`packages/web/src/app/intake/[jobId]/layout.tsx`)
- [ ] **Step 1: Details** (`/intake/[jobId]/details/page.tsx`)
  - [ ] Form for job title, company, description
  - [ ] Validation with Zod
  - [ ] Save to API and navigate to next step
- [ ] **Step 2: Experience** (`/intake/[jobId]/experience/page.tsx`)
  - [ ] List user experiences with checkboxes
  - [ ] Run gap analysis workflow
  - [ ] Display gap analysis results
  - [ ] Experience selection
  - [ ] Generate resume button
  - [ ] Navigate to proposals after resume generation
- [ ] **Step 3: Proposals** (`/intake/[jobId]/proposals/page.tsx`)
  - [ ] Display experience proposals
  - [ ] Accept/reject individual proposals
  - [ ] Accept all button
  - [ ] Complete intake and navigate to job detail

### Phase 8: CORS & Environment Configuration

- [ ] Update FastAPI CORS to allow localhost:3000
- [ ] Add Vercel domain to CORS origins
- [ ] Test API calls from Next.js to FastAPI
- [ ] Document environment variable setup in README

### Phase 9: Testing & Verification

- [ ] Manual testing of all pages and workflows
- [ ] Test job intake flow end-to-end
- [ ] Test resume generation
- [ ] Test cover letter generation
- [ ] Test profile management
- [ ] Verify all API integrations work
- [ ] Test on different browsers
- [ ] Test responsive design on mobile

### Phase 10: Streamlit Removal

- [ ] Verify Next.js has feature parity with Streamlit
- [ ] Delete `packages/api/app/` directory
- [ ] Remove Streamlit dependencies from `packages/api/pyproject.toml`
- [ ] Update README to remove Streamlit documentation

### Phase 11: Documentation

- [ ] Update main README with new architecture
- [ ] Document how to run the application
- [ ] Document how to deploy to Vercel
- [ ] Document environment variables
- [ ] Document type generation workflow
- [ ] Add architecture diagram
- [ ] Document future plans (Supabase, browser extension)

## Code Standards

**See `standards.md` in this directory for complete coding standards.**

Key standards include: file naming conventions, component structure order, state management patterns (TanStack Query / Zustand / useState), TypeScript usage, API client patterns, and form handling with React Hook Form + Zod.

## Design Guidelines

### Styling Principles

- **Minimalist:** Clean, uncluttered interfaces
- **Modern:** Use contemporary web design patterns
- **Consistent:** Uniform spacing, typography, and colors
- **Responsive:** Mobile-first design approach
- **Accessible:** Follow WCAG guidelines, proper contrast, keyboard navigation

### ShadCN Customization

Start with default New York style and Slate color scheme. Customize only:

- Primary color (if needed for branding)
- Border radius (if wanting more/less rounded corners)
- Spacing scale (use Tailwind defaults)

Keep component styling minimal - rely on ShadCN defaults.

### Component Organization

```
packages/web/src/components/
├── ui/                  # ShadCN components (auto-generated)
├── job-detail/          # Job detail tab components
│   ├── OverviewTab.tsx
│   ├── ResumeTab.tsx
│   ├── CoverLetterTab.tsx
│   └── NotesTab.tsx
├── intake/              # Intake workflow components
│   ├── DetailsStep.tsx
│   ├── ExperienceStep.tsx
│   └── ProposalsStep.tsx
├── profile/             # Profile page components
├── jobs/                # Jobs list components
└── layout/              # Layout components (nav, footer)
```

## Success Criteria

1. **Feature Parity:** All in-scope Streamlit features replicated in Next.js
2. **Type Safety:** Full TypeScript coverage, no `any` types
3. **Performance:** Fast page loads, smooth interactions
4. **Responsive:** Works on desktop, tablet, and mobile
5. **Clean Code:** Well-organized, maintainable codebase
6. **Documentation:** Clear setup and development instructions
7. **Deployment Ready:** Can deploy to Vercel with minimal configuration

## Risks & Mitigations

**Risk:** Next.js learning curve may slow development
**Mitigation:** Follow Next.js documentation closely, use established patterns, keep it simple

**Risk:** Type generation may have inconsistencies with Python schemas
**Mitigation:** Regularly regenerate types, test API contracts, validate responses

**Risk:** Job intake workflow complexity in route-based approach
**Mitigation:** Use Zustand for state management, persist session data via API, implement navigation guards

**Risk:** Repository restructuring may break existing functionality
**Mitigation:** Test thoroughly after restructuring, update all imports carefully, maintain Git history

## Future Enhancements (Not This Sprint)

- Templates page
- Responses page
- Messages tab on job detail
- Testing infrastructure (Jest, React Testing Library, Playwright)
- Supabase authentication and database migration
- Browser extension integration
- Advanced analytics and tracking
- Enhanced resume editor with rich text
- Real-time collaboration features
