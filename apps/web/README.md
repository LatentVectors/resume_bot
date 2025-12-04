# Resume Bot - Web Frontend

Next.js frontend application for Resume Bot, built with React, TypeScript, and ShadCN UI.

## Prerequisites

- Node.js 18+ and npm/pnpm/yarn
- FastAPI backend running on port 8000 (see `packages/api/README.md` or root `README.md`)

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure Environment

Create `.env.local` in this directory:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

For production, set this to your deployed API URL:
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### 3. Generate TypeScript Types

Before starting development, generate TypeScript types from the FastAPI OpenAPI schema:

1. Ensure the FastAPI backend is running on port 8000
2. Run the type generation script:
```bash
npm run generate:types
```

This creates/updates `src/types/api.ts` with types matching your API schemas.

**When to regenerate types:**
- After backend API schema changes
- When adding new endpoints
- Before starting frontend development after backend changes

### 4. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

The page auto-updates as you edit files.

### 5. (Optional) Run Both Frontend and Backend Together

If you have `concurrently` installed and the script configured in `package.json`, you can run both services:

```bash
npm run dev:all
```

This starts both the Next.js dev server and the FastAPI backend.

## Available Scripts

- `npm run dev` - Start Next.js development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint
- `npm run generate:types` - Generate TypeScript types from FastAPI OpenAPI schema

## Project Structure

```
packages/web/
├── src/
│   ├── app/              # Next.js App Router pages
│   │   ├── layout.tsx    # Root layout with navigation
│   │   ├── page.tsx      # Home page
│   │   ├── profile/      # Profile page
│   │   ├── jobs/         # Jobs list and detail pages
│   │   └── intake/       # Job intake workflow
│   ├── components/       # React components
│   │   ├── ui/           # ShadCN UI components
│   │   ├── layout/       # Layout components (nav, etc.)
│   │   ├── jobs/         # Job-related components
│   │   ├── profile/      # Profile page components
│   │   └── job-detail/   # Job detail tab components
│   ├── lib/              # Utilities and configuration
│   │   ├── api/          # API client functions
│   │   ├── hooks/        # Custom React hooks
│   │   ├── store/        # Zustand stores
│   │   └── providers.tsx # React Query provider
│   └── types/            # TypeScript types
│       ├── api.ts        # Generated API types (from FastAPI)
│       └── index.ts      # Shared app types
├── public/               # Static assets
├── package.json
├── tsconfig.json
└── .env.local            # Environment variables (create this)
```

## Technology Stack

- **Framework**: Next.js 14+ (App Router)
- **Language**: TypeScript 5+
- **UI**: ShadCN UI (New York style, Slate theme) + Tailwind CSS
- **State Management**: 
  - TanStack Query (React Query) for server state
  - Zustand for client state
- **Forms**: React Hook Form + Zod validation
- **Type Generation**: openapi-typescript

## Development

### Type Safety

All types are generated from the Supabase database schema in `packages/database`. Import types like:

```typescript
import type { Job, JobInsert, JobStatus } from "@resume/database/types";

// Or use the convenience re-exports from the web app:
import type { Job } from "@/types";
```

### API Client

API calls are made through typed client functions in `src/lib/api/`. Use TanStack Query hooks in components:

```typescript
import { useQuery } from "@tanstack/react-query";
import { jobsAPI } from "@/lib/api/jobs";

function JobsList() {
  const { data: jobs, isLoading } = useQuery({
    queryKey: ["jobs", userId],
    queryFn: () => jobsAPI.list(userId),
  });
  // ...
}
```

### Custom Hooks

Reusable data fetching hooks are in `src/lib/hooks/`:
- `useJobs` - Fetch jobs list
- `useJob` - Fetch single job
- `useExperiences` - Fetch experiences
- `useUser` - Fetch current user

### State Management

- **Server State**: Use TanStack Query for all API data
- **Client State**: Use Zustand stores in `src/lib/store/`
  - `useUserStore` - Current user information
  - `useIntakeStore` - Job intake workflow state

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |

All environment variables must be prefixed with `NEXT_PUBLIC_` to be accessible in the browser.

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Set `NEXT_PUBLIC_API_URL` environment variable in Vercel dashboard
3. Deploy automatically on push to main branch

### Other Platforms

Build the application:
```bash
npm run build
npm run start
```

Ensure `NEXT_PUBLIC_API_URL` is set in your deployment environment.

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [ShadCN UI](https://ui.shadcn.com/)
- [TanStack Query](https://tanstack.com/query/latest)
- [Zustand](https://github.com/pmndrs/zustand)
