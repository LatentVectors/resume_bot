# API Refactor: Python to Next.js + Supabase Migration

## Overview

Migrate all API logic from the Python FastAPI backend (`apps/api/api/`) to Next.js API routes (`apps/web/src/app/api/`), replacing SQLite with Supabase PostgreSQL as the database layer. This consolidates the backend into the Next.js application and establishes a production-grade database foundation.

## Migration Strategy

**Full Cutover Migration**: Migrate all routes before switching over. The Python API continues to be the sole backend until all Next.js routes are complete and tested, then perform a complete cutover.

## Supabase Integration

### Database

- Replace SQLite with Supabase PostgreSQL
- All existing entities will be migrated to Supabase tables
- SQLite database contains production data and must NOT be modified or deleted during migration

### Authentication (Future)

- Currently uses a single hardcoded user
- Will adopt Supabase Auth when implementing authentication
- Design schema with multi-tenancy and Row Level Security (RLS) in mind for future scalability

### Account Model Decision

This migration maintains a **user-centric model** (`user_id`) rather than MakerKit's account-centric model (`account_id`). During the eventual MakerKit port:

- `user_id` columns will be renamed to `account_id`
- An `accounts` table will be created
- Personal accounts will have `account_id = user_id`

This approach minimizes changes now while documenting the future migration path.

### User Context During Migration

Use an environment variable (`CURRENT_USER_ID`) to configure the active user during migration. This maintains single-user operation while preparing for future Supabase Auth integration.

### Storage (Future)

- Not currently needed - PDFs are generated on-demand in browser
- Will use Supabase Storage when file storage is required

## Database Package Structure

Create a dedicated Turborepo package for database concerns:

```
packages/database/
├── supabase/
│   ├── config.toml
│   ├── migrations/
│   │   └── YYYYMMDDHHMMSS_initial_schema.sql
│   └── seed.sql
├── src/
│   ├── index.ts              # Re-exports all public APIs
│   ├── client.ts             # Browser Supabase client
│   ├── server-client.ts      # Server Supabase client
│   ├── admin-client.ts       # Admin Supabase client (elevated privileges)
│   ├── types/
│   │   ├── index.ts          # Type re-exports and convenience aliases
│   │   └── database.types.ts # Supabase-generated types
│   └── hooks/
│       └── use-supabase.ts   # React hook for browser client
├── scripts/
│   └── migrate-from-sqlite.ts
├── package.json
└── tsconfig.json
```

### Package Exports (package.json)

```json
{
  "name": "@resume/database",
  "exports": {
    ".": "./src/index.ts",
    "./server": "./src/server-client.ts",
    "./admin": "./src/admin-client.ts",
    "./client": "./src/client.ts",
    "./hooks": "./src/hooks/use-supabase.ts",
    "./types": "./src/types/index.ts"
  }
}
```

Apps import from this package:

```typescript
import { getSupabaseServerClient } from "@resume/database/server";
import type { Job, JobInsert } from "@resume/database/types";
```

## Data Persistence Layer Architecture

Implement MakerKit-style patterns independently in `packages/database/` using official Supabase packages (`@supabase/supabase-js`, `@supabase/ssr`).

### Supabase Clients

**Browser (Client Components):**

```typescript
import { useSupabase } from "@resume/database/hooks";

export function MyComponent() {
  const supabase = useSupabase();
  // ...
}
```

**Server (Server Actions, Route Handlers, Server Components):**

```typescript
import { getSupabaseServerClient } from "@resume/database/server";

export async function myServerAction() {
  const supabase = getSupabaseServerClient();
  const { data, error } = await supabase.from("jobs").select("*");
}
```

**Admin Client (elevated privileges, use sparingly):**

```typescript
import { getSupabaseServerAdminClient } from "@resume/database/admin";
```

### Data Loading (Server Components)

Use direct Supabase queries in server components. For paginated data, implement pagination helpers as needed.

### Data Mutations (Server Actions)

- Define Server Actions in files with `'use server'` directive
- Use Zod schemas for validation (convention: `*.schema.ts` files)
- Use `revalidatePath()` to refresh data after mutations
- Organize server actions in `_lib/server/` directories

### Type Generation

Generate types from Supabase schema into the database package:

```bash
cd packages/database
pnpm supabase gen types typescript --local > src/types/database.types.ts
```

Export convenience type aliases from `src/types/index.ts`:

```typescript
export type { Database } from "./database.types";

// Convenience aliases for common types
type Tables = Database["public"]["Tables"];

export type Job = Tables["jobs"]["Row"];
export type JobInsert = Tables["jobs"]["Insert"];
export type JobUpdate = Tables["jobs"]["Update"];

export type Experience = Tables["experiences"]["Row"];
export type ExperienceInsert = Tables["experiences"]["Insert"];
export type ExperienceUpdate = Tables["experiences"]["Update"];

// ... etc for all entities
```

Access raw types via: `Database['public']['Tables']['tablename']['Row']`

### File Organization (per feature/entity)

```
src/app/api/[entity]/
├── route.ts              # GET (list), POST (create)
├── [id]/
│   └── route.ts          # GET (single), PATCH (update), DELETE
└── _lib/
    ├── schema/
    │   └── [entity].schema.ts   # Zod validation schemas
    └── server/
        └── actions.ts           # Server actions (if needed alongside routes)
```

### Server Actions vs API Routes

**Use API Routes (`route.ts`)** for:

- External API consumers (mobile apps, integrations)
- Complex multi-step operations
- Compatibility with existing frontend client patterns

**Use Server Actions (`'use server'`)** for:

- Form submissions from React Server Components
- Simple mutations with `revalidatePath()`
- New features being built fresh

For this migration, **default to API Routes** to maintain compatibility with the existing frontend API client. Server Actions can be adopted incrementally for new features.

## API Route Organization

Follow Next.js App Router conventions with one file per entity:

- `src/app/api/users/route.ts` (list, create)
- `src/app/api/users/[id]/route.ts` (get, update, delete)
- `src/app/api/jobs/route.ts`, `src/app/api/jobs/[id]/route.ts`
- etc.

### Non-Standard Endpoints

The current Python API has specialized endpoints beyond standard CRUD. These will be migrated as nested routes:

```
src/app/api/jobs/
├── route.ts                           # GET (list), POST (create)
├── bulk-delete/
│   └── route.ts                       # DELETE (bulk delete)
├── [id]/
│   ├── route.ts                       # GET, PATCH, DELETE
│   ├── favorite/
│   │   └── route.ts                   # PATCH (toggle favorite)
│   ├── status/
│   │   └── route.ts                   # PATCH (update status)
│   ├── apply/
│   │   └── route.ts                   # POST (mark as applied)
│   └── intake-session/
│       ├── route.ts                   # GET, POST, PATCH
│       └── [sessionId]/
│           └── messages/
│               └── route.ts           # GET, POST
```

### Frontend Client Updates

Update existing `lib/api/` client functions to call new Next.js API routes (change base URL from `http://localhost:8000/api/v1/...` to `/api/...`). React Query hooks remain largely unchanged.

## Entities to Migrate

### Database Entities (All)

- Users
- Jobs
- Experiences
- Achievements
- Education
- Certifications
- Resumes
- Resume Versions
- Cover Letters
- Cover Letter Versions
- Messages
- Responses
- Notes
- Job Intake Sessions
- Job Intake Chat Messages
- Experience Proposals
- Templates (migrate from file-based storage to database)

### Templates Migration

**Current Location**:

- Resume templates: `apps/api/src/features/resume/templates/` (7 files: `resume_000.html` - `resume_006.html`)
- Cover letter templates: `apps/api/src/features/cover_letter/templates/` (1 file: `cover_000.html`)

**Migration Strategy**:

1. Read HTML content from existing files
2. Insert into `templates` table with `name` matching filename (e.g., `resume_000.html`)
3. Existing `template_name` references in `resumes` and `cover_letters` tables remain valid

### Out of Scope

- **Prompts**: Currently file-based, will remain as files. Refactoring prompts is out of scope for this sprint.

## Type Generation Strategy

Replace the current OpenAPI-generated types (`openapi-typescript` from Python API) with Supabase-generated types:

1. Delete or deprecate `apps/web/src/types/api.ts` (OpenAPI-generated)
2. Generate types from Supabase schema: `supabase gen types typescript`
3. Export types from `packages/database/types`
4. Update all imports throughout the codebase

## Existing Next.js Routes

The following existing API routes will be **refactored** to use the new Supabase data persistence layer during this migration:

- `/api/chat/` - Update to use Supabase for any persistence
- `/api/langgraph/` - Update database access patterns
- `/api/workflows/` (gap-analysis, stakeholder-analysis, etc.) - Update as needed

These routes currently call the Python API for database operations. During Phase 5, they will be updated to use `getSupabaseServerClient()` directly.

## Schema Design (PostgreSQL Best Practices)

The PostgreSQL schema should leverage native PostgreSQL features rather than directly copying SQLite patterns:

### Data Type Upgrades

| SQLite Pattern            | PostgreSQL Upgrade                                  |
| ------------------------- | --------------------------------------------------- |
| TEXT storing JSON strings | `JSONB` native type                                 |
| TEXT for enums            | PostgreSQL `ENUM` types or `TEXT CHECK` constraints |
| TEXT for dates            | `DATE`, `TIMESTAMP WITH TIME ZONE`                  |
| INTEGER boolean (0/1)     | Native `BOOLEAN`                                    |
| JSON array as TEXT        | `JSONB` array or PostgreSQL arrays                  |

### Primary Key Strategy

Use `SERIAL` (auto-incrementing integer) primary keys to match existing SQLite IDs. This maintains URL compatibility (`/jobs/123`) and simplifies data migration.

```sql
CREATE TABLE jobs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  -- ...
);
```

**Future Consideration**: MakerKit uses UUIDs. When porting to MakerKit, a migration script will convert integer IDs to UUIDs.

### Schema Conventions

- Use `snake_case` for table and column names
- Include `created_at` and `updated_at` timestamps with defaults
- Add `user_id` foreign key to all user-owned tables (prepares for RLS)
- Use PostgreSQL-native constraints and indexes
- Create appropriate foreign key relationships with `ON DELETE` behaviors

### Row Level Security Preparation

- All user-owned tables include `user_id` column
- RLS policies will be added when Supabase Auth is implemented
- Schema designed to support future multi-tenancy

### Templates Table Schema

Templates migrate from file-based storage to database with structured metadata:

```sql
CREATE TABLE templates (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,  -- e.g., "resume_003.html" for backward compatibility
  type TEXT NOT NULL CHECK (type IN ('resume', 'cover_letter')),
  html_content TEXT NOT NULL,
  description TEXT,
  preview_image_url TEXT,
  is_default BOOLEAN DEFAULT FALSE,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Foreign Key Cascade Behaviors

| Relationship                                     | ON DELETE Behavior |
| ------------------------------------------------ | ------------------ |
| `jobs → users`                                   | CASCADE            |
| `experiences → users`                            | CASCADE            |
| `achievements → experiences`                     | CASCADE            |
| `resumes → jobs`                                 | CASCADE            |
| `resume_versions → jobs`                         | CASCADE            |
| `cover_letters → jobs`                           | CASCADE            |
| `cover_letter_versions → jobs`                   | CASCADE            |
| `messages → jobs`                                | CASCADE            |
| `notes → jobs`                                   | CASCADE            |
| `job_intake_sessions → jobs`                     | CASCADE            |
| `job_intake_chat_messages → job_intake_sessions` | CASCADE            |
| `experience_proposals → job_intake_sessions`     | CASCADE            |
| `experience_proposals → experiences`             | SET NULL           |

Note: Deleting a user cascades to all their jobs, which cascades to all job-related data.

## API Response Format

Adopt Next.js/REST conventions for API responses:

- **List endpoints**: Return array directly, with pagination via query params (`?page=1&limit=20`)
- **Single resource**: Return object directly
- **Create/Update**: Return created/updated resource
- **Delete**: Return `204 No Content`
- **Errors**: Use standard HTTP status codes with `{ error: string, details?: object }`

Example response structures:

```typescript
// GET /api/jobs (list)
Job[]

// GET /api/jobs/123 (single)
Job

// POST /api/jobs (create)
Job

// PATCH /api/jobs/123 (update)
Job

// DELETE /api/jobs/123
// 204 No Content

// Error response
{ error: "Job not found", code: "NOT_FOUND" }
```

## Data Migration

### Migration Script

Create a TypeScript migration script at `packages/database/scripts/migrate-from-sqlite.ts`:

```typescript
// Uses sql.js (pure JavaScript SQLite) for portability - no native bindings required
import initSqlJs from "sql.js";
import { createClient } from "@supabase/supabase-js";

// - Reads SQLite file using sql.js
// - Transforms data types (JSON strings → objects, dates → Date objects)
// - Handles foreign key insertion order (users first, then dependent tables)
// - Inserts into Supabase using the Supabase client
// - Outputs validation report with row counts per table
```

Run via: `pnpm --filter @resume/database run migrate:from-sqlite`

**Dependencies** (in `packages/database/package.json`):

```json
{
  "devDependencies": {
    "sql.js": "^1.10.0"
  }
}
```

### Migration Steps

1. Export data from SQLite database (read-only)
2. Transform data types (JSON strings → JSONB, date strings → timestamps, etc.)
3. Import data into Supabase PostgreSQL with type conversions
4. Validate data integrity post-migration (row counts, relationship integrity)

The existing SQLite database must remain intact and unmodified.

## Migration Phases

The migration will be executed in phases to maintain manageable units of work:

### Phase 1: Supabase Setup & Database Schema

- Set up Supabase local development environment
- Create PostgreSQL schema matching existing SQLite models
- Generate TypeScript types from schema
- Create data migration script (SQLite → Supabase)
- Execute data migration and validate integrity

### Phase 2: Core Entity Routes

Migrate fundamental entities that other entities depend on:

- Users
- Experiences
- Achievements
- Education
- Certifications

### Phase 3: Job-Related Routes

Migrate job application tracking entities:

- Jobs (including non-standard endpoints: favorite, status, apply)
- Resumes
- Resume Versions
- Cover Letters
- Cover Letter Versions

### Phase 4: Supporting Entity Routes

Migrate remaining entities:

- Messages
- Responses
- Notes
- Job Intake Sessions
- Job Intake Chat Messages
- Experience Proposals
- Templates (includes migrating from file storage to database)

### Phase 5: Frontend Integration & Cleanup

- Update frontend API clients to use new routes
- Refactor existing Next.js routes (`/api/chat/`, `/api/langgraph/`, `/api/workflows/`) to use Supabase
- Test full application flow
- Remove Python API directory
- Update documentation

## Environment Variables

Required environment variables for the migration:

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<local-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<local-service-role-key>

# User Context (temporary, until Supabase Auth)
CURRENT_USER_ID=1

# Migration Script (used only during data migration)
SQLITE_DATABASE_PATH=./apps/api/data/resume.db
```

## Supabase Local Development

Since no Supabase project exists yet, use Supabase local development:

```bash
# Initialize Supabase in packages/database/
cd packages/database
supabase init

# Start local Supabase instance
supabase start

# Generate types after schema changes
supabase gen types typescript --local > src/types/database.types.ts
```

**Key Development URLs:**

- Supabase Studio: http://localhost:54323
- Supabase API: http://localhost:54321

## Post-Migration Cleanup

After successful migration and validation:

- Remove `/apps/api/` Python directory from the project
- LangGraph agents have already been migrated to `/apps/agents/` directory
- Update documentation and remove Python-related dependencies
- Remove `openapi-typescript` dependency and related scripts from `apps/web/package.json`

## Testing

Manual testing will be performed during the sprint. No automated tests are required for this migration.

## MakerKit Alignment Notes

This migration follows MakerKit conventions where practical to ease the eventual full MakerKit port.

### Aligned Patterns

- ✅ Supabase local development workflow
- ✅ Server client patterns (`getSupabaseServerClient`)
- ✅ Type generation from database schema
- ✅ Zod schemas for validation (convention: `*.schema.ts`)
- ✅ `revalidatePath()` for cache invalidation
- ✅ Package structure with client/server exports

### Deferred Patterns (future MakerKit migration)

- ⏳ Account-centric model (currently user-centric with `user_id`)
- ⏳ UUID primary keys (currently integer for SQLite compatibility)
- ⏳ Row Level Security policies (deferred until Supabase Auth)
- ⏳ `@kit/` package namespace (using `@resume/` for now)
- ⏳ ServerDataLoader component (using direct Supabase queries)

### Breaking Changes During MakerKit Port

When fully porting to MakerKit, expect:

1. `user_id` → `account_id` column renames across all tables
2. Integer IDs → UUID migrations for all primary keys
3. Add `accounts` and `accounts_memberships` tables
4. Enable RLS policies on all tables
5. Rename `@resume/database` → `@kit/supabase` imports

## Reference

- [MakerKit Docs: Local Development](https://makerkit.dev/docs/next-supabase-turbo/development/approaching-local-development)
- [MakerKit Docs: Database Architecture](https://makerkit.dev/docs/next-supabase-turbo/development/database-architecture)
- [MakerKit Docs: Loading Data](https://makerkit.dev/docs/next-supabase-turbo/development/loading-data-from-database)
- [MakerKit Docs: Writing Data](https://makerkit.dev/docs/next-supabase-turbo/development/writing-data-to-database)
