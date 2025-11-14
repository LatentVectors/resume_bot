# Next.js & React Code Standards

Code style and organizational standards for the Next.js frontend. Only includes decisions that aren't obvious or where developers might reasonably disagree.

## File Naming

- **Components:** PascalCase (`JobCard.tsx`, `ExperienceList.tsx`)
- **Pages:** lowercase (`page.tsx`, `layout.tsx`, `[id]/page.tsx`)
- **Hooks:** camelCase with `use` prefix (`useJobs.ts`, `useDebounce.ts`)
- **Utils:** camelCase (`formatDate.ts`, `apiClient.ts`)
- **Constants:** SCREAMING_SNAKE_CASE for exports, camelCase for filenames

## Component Structure

Order components consistently:

1. `'use client'` directive (if needed)
2. Imports (organized by: React/Next, external libs, UI components, custom components, hooks/utils, API clients, types)
3. Type/interface definitions
4. Component function
5. Hooks (state → queries → mutations → effects)
6. Derived state
7. Event handlers
8. Early returns
9. JSX return

Keep components under 200 lines. Extract sub-components or custom hooks when growing larger.

## State Management

**Three-tier approach:**

1. **TanStack Query** - All API data (jobs, experiences, resumes). Never duplicate API data elsewhere.
2. **Zustand** - Shared app state (current user, workflow state, UI state spanning components)
3. **useState** - Local component UI state only

**Forms:** Always use React Hook Form + Zod validation + ShadCN Form components.

**Query keys:** Use arrays with resource type first: `['jobs']`, `['jobs', jobId]`, `['jobs', jobId, 'resumes']`

## Data Fetching

- Mark all page components as `'use client'` (this is a user-specific, interactive app)
- Create reusable query hooks: `useJobs()`, `useJob(id)`
- Create mutation hooks: `useCreateJob()`, `useUpdateJob()`
- Handle loading/error states in components

## TypeScript

**Never use `any`** - Use `unknown` and type guards if needed.

**Type vs Interface:**

- Use `interface` for object shapes (default choice for component props, data models)
- Use `type` only for unions, intersections, primitives, mapped types, or when you need type-specific features
- When in doubt, use `interface`

**Shared Types - Critical:**

- **Always check `src/types/` before creating a new type**
- Use generated API types from `src/types/api.ts` (from openapi-typescript)
- If a type is used in 2+ places, it belongs in a shared location
- Never duplicate type definitions - move to shared location instead
- Type imports: `import type { JobResponse } from '@/types/api'`

**Type Organization:**

- API response/request types: `src/types/api.ts` (auto-generated)
- Shared app types: `src/types/index.ts`
- Component-specific types: Define in component file only if truly unique to that component

**Example:**

```typescript
// ❌ Bad - Duplicating types across files
// components/JobCard.tsx
interface Job {
  id: number;
  title: string;
}

// components/JobList.tsx
interface Job {
  id: number;
  title: string;
} // Duplicate!

// ✅ Good - Single source of truth
// types/api.ts (generated)
type JobResponse = components["schemas"]["JobResponse"];

// Both files import:
import type { JobResponse } from "@/types/api";
```

## API Client

- All API calls through typed functions in `lib/api/`
- Use generated types: `type JobResponse = components['schemas']['JobResponse']`
- Return typed promises: `apiRequest<JobResponse>(endpoint)`

## Styling

- Use Tailwind utility classes exclusively
- Use `cn()` utility for conditional classes
- No inline styles unless absolutely necessary
- Customize ShadCN components minimally - rely on defaults

## Naming Conventions

- **Boolean variables:** `is`, `has`, `should` prefix
- **Event handlers:** `handle` prefix (`handleClick`, `handleSubmit`)
- **Components returning JSX:** Use function declarations, not arrows
- **Utilities/helpers:** Use arrow functions

## Import Organization

Group imports with blank lines between groups:

1. React/Next.js
2. External libraries
3. UI components (ShadCN)
4. Custom components
5. Hooks and utilities
6. API clients
7. Types (with `type` keyword)

## Forms

Standard pattern for all forms:

```typescript
// Define Zod schema
const schema = z.object({ /* fields */ });
type FormData = z.infer<typeof schema>;

// Use React Hook Form with resolver
const form = useForm<FormData>({
  resolver: zodResolver(schema),
  defaultValues: { /* defaults */ },
});

// Use ShadCN Form components
<Form {...form}>
  <form onSubmit={form.handleSubmit(onSubmit)}>
    <FormField control={form.control} name="fieldName" ... />
  </form>
</Form>
```

## Common Patterns

**Client Component Directive:**
All interactive components need `'use client'` at the top (before imports).

**Error Handling:**
Let TanStack Query handle API errors. Show user-friendly messages with toast notifications on mutations.

**Loading States:**
Use TanStack Query's `isLoading` state. Disable form submit buttons during `formState.isSubmitting`.

**Conditional Rendering:**
Use early returns for loading/error/empty states. Keep JSX clean.

## Things to Avoid

- Don't create objects/arrays directly in JSX (causes re-renders)
- Don't mutate state directly - always create new objects/arrays
- Don't duplicate derived state in useState - calculate it
- Don't use `useEffect` for data fetching - use TanStack Query
- Don't prop drill - use Zustand for deeply nested state
- Don't use `@ts-ignore` - fix the type issue
- Don't use excessive non-null assertions (`!`)

## Accessibility Basics

- Use semantic HTML (`<button>`, `<nav>`, `<main>`)
- Include `alt` text for images
- Add `aria-label` for icon-only buttons
- Ensure keyboard navigation works

## Navigation & Routing

**Link vs useRouter:**

- Use `<Link>` for navigation in JSX
- Use `router.push()` only after async operations (form submission, API calls)
- Use `router.replace()` when you don't want history entry

**Search Params:**

- Use `useSearchParams()` hook to read params
- Use `router.push()` with query strings to update: `router.push(`/jobs/${id}?tab=resume`)`
- Keep param names consistent: camelCase for multi-word params

## Async Handling

**Event Handlers:**
Don't use async directly in event handlers. Extract the async logic:

```typescript
// ✅ Good
const handleSubmit = (data: FormData) => {
  createMutation.mutate(data); // Mutation handles async
};

// ❌ Avoid
const handleSubmit = async (data: FormData) => {
  await createJob(data); // Loses error handling
};
```

**Promises in onClick:**
Use mutations for API calls, not raw promises in handlers.

## Null vs Undefined

- Use `null` for intentionally empty values (cleared user selection, no data loaded yet)
- Use `undefined` for optional props and uninitialized state
- Use optional chaining (`?.`) liberally for object property access
- Avoid non-null assertion (`!`) unless you're absolutely certain

## Custom Hooks

**Return values:**

- Return objects for multiple values: `{ data, isLoading, error }`
- Return single value directly for simple hooks: `useDebounce(value)` returns the value
- Keep return values consistent with similar hooks (follow TanStack Query patterns)

## Loading & Empty States

**Patterns:**

- Use skeleton loaders for content areas (ShadCN Skeleton component)
- Use spinners for buttons and small actions
- Show empty states with helpful messages and CTAs
- Always handle loading, error, and empty states explicitly

## Modals & Dialogs

**State Management:**

- Store open/closed state in parent component with useState
- Pass `open` and `onOpenChange` to ShadCN Dialog
- For multi-step modals (job intake), use Zustand or URL-based routing
- Close dialogs after successful mutations

## User Feedback

**Toasts:**

- Show success toast after mutations complete
- Show error toast when mutations fail
- Keep messages concise and actionable
- Use for async operations only (not for validation errors - those show inline)

**Error Messages:**

- User-facing: Simple, actionable ("Failed to save job. Please try again.")
- Console: Detailed with context (`logger.error()`)
- Form validation: Show next to fields (FormMessage component)

## Date & Number Formatting

- Use browser's `Intl.DateTimeFormat` for dates
- Use `Intl.NumberFormat` for numbers/currency
- Store dates as ISO strings from API
- Display in user's locale (default browser behavior)

## Environment Variables

- Prefix client-accessible vars with `NEXT_PUBLIC_`
- Never expose secrets in client-side env vars
- Document required env vars in README
- Use `process.env.NEXT_PUBLIC_API_URL` with fallback

## Console & Logging

**In Production Code:**

- No `console.log()` - remove before committing
- No `console.warn()` unless truly needed
- Use for debugging only, then remove

**Acceptable:**

- `console.error()` for caught errors with context (rare)
- Development-only logs behind `if (process.env.NODE_ENV === 'development')`

## Component Patterns

**Children Props:**

- Use `children: React.ReactNode` for component wrappers
- Use render props only when children need access to parent state
- Prefer composition over render props

**Prop Spreading:**

- OK for passing through component props: `<Input {...field} />`
- Avoid for generic objects: `<Component {...someRandomObject} />`
- Be explicit about what props you're accepting

## Code Style Details

- **Quotes:** Double quotes for strings
- **Semicolons:** Yes
- **Trailing commas:** Yes
- **Line length:** 100 characters (Prettier will handle)
- **Function declarations:** Use for components, arrows for utils/handlers
- **Boolean checks:** Use `!!` sparingly, prefer explicit `!= null` or `!== undefined` when intent matters
- **Array methods:** Use `map` for transformations, avoid `forEach` in React code
