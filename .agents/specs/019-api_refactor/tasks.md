# Spec Tasks

Task Organization
Tasks 1-4: Phase 1 (Supabase Setup & Database Schema)
Tasks 5-6: Phase 2 (Core Entity Routes)
Tasks 7-10: Phase 3 (Job-Related Routes)
Task 11: Phase 4 (Supporting Entity Routes)
Task 12: Phase 5 (Frontend Integration & Cleanup)

Key Dependencies
Tasks should be executed in order as:
Tasks 1-4 must complete before any API routes
Task 5 (Users) should complete before entities that reference users
Tasks 7-8 (Jobs) should complete before Task 9 (Intake System) and Task 10 (Resumes/Cover Letters)
Task 12 (Cleanup) is the final step after all routes are implemented

## Tasks

- [x] 1. Database Package Setup

  - [x] 1.1 Create `packages/database/` directory structure with `src/`, `supabase/`, `scripts/` folders
  - [x] 1.2 Create `package.json` with name `@resume/database`, exports configuration, and dependencies (`@supabase/supabase-js`, `@supabase/ssr`, `zod`)
  - [x] 1.3 Create `tsconfig.json` extending root TypeScript config
  - [x] 1.4 Run `supabase init` in `packages/database/` to generate `supabase/config.toml`
  - [x] 1.5 Add `@resume/database` to `apps/web/package.json` dependencies
  - [x] 1.6 Update root `turbo.json` to include the new package in the pipeline

- [x] 2. PostgreSQL Schema Migration

  - [x] 2.1 Create initial migration file `supabase/migrations/YYYYMMDDHHMMSS_initial_schema.sql`
  - [x] 2.2 Define `users` table with all columns from SQLite model (first_name, last_name, contact fields, timestamps)
  - [x] 2.3 Define `experiences` table with `user_id` FK, date fields, `skills` as JSONB array
  - [x] 2.4 Define `achievements` table with `experience_id` FK and `order` column
  - [x] 2.5 Define `education` and `certifications` tables with `user_id` FK
  - [x] 2.6 Define `jobs` table with all columns including `status` CHECK constraint, `resume_chat_thread_id`
  - [x] 2.7 Define `resumes`, `resume_versions`, `cover_letters`, `cover_letter_versions` tables with appropriate FKs and unique constraints
  - [x] 2.8 Define remaining tables: `messages`, `responses`, `notes`, `job_intake_sessions`, `job_intake_chat_messages`, `experience_proposals`, `templates`

- [x] 3. Supabase Clients Implementation

  - [x] 3.1 Create `src/client.ts` with browser Supabase client using `createBrowserClient` from `@supabase/ssr`
  - [x] 3.2 Create `src/server-client.ts` with `getSupabaseServerClient()` using `createServerClient` and cookies
  - [x] 3.3 Create `src/admin-client.ts` with `getSupabaseServerAdminClient()` using service role key
  - [x] 3.4 Create `src/hooks/use-supabase.ts` React hook for client components
  - [x] 3.5 Create `src/types/index.ts` with type re-exports and convenience aliases (Job, JobInsert, JobUpdate, etc.)
  - [x] 3.6 Create `src/index.ts` re-exporting all public APIs
  - [x] 3.7 Add environment variables to `apps/web/.env.local` (NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY)

- [x] 4. SQLite Data Migration

  - [x] 4.1 Add `sql.js` as dev dependency in `packages/database/package.json`
  - [x] 4.2 Create `scripts/migrate-from-sqlite.ts` with sql.js initialization and SQLite file reading
  - [x] 4.3 Implement data transformation functions (JSON strings → objects, date strings → timestamps, enum validation)
  - [x] 4.4 Implement insertion logic respecting foreign key order (users → experiences → achievements, users → jobs → resumes, etc.)
  - [x] 4.5 Add validation reporting (row counts per table, FK integrity checks)
  - [x] 4.6 Add `migrate:from-sqlite` script to `package.json`
  - [x] 4.7 Run migration, verify data integrity, generate types with `supabase gen types typescript --local`

- [x] 5. Users & Profile Entities Routes

  - [x] 5.1 Create `apps/web/src/app/api/users/route.ts` with GET (list) and POST (create) handlers
  - [x] 5.2 Create `apps/web/src/app/api/users/[id]/route.ts` with GET, PATCH, DELETE handlers
  - [x] 5.3 Create `apps/web/src/app/api/users/_lib/schema/user.schema.ts` with Zod validation schemas
  - [x] 5.4 Create `apps/web/src/app/api/education/route.ts` and `[id]/route.ts` with CRUD handlers
  - [x] 5.5 Create `apps/web/src/app/api/education/_lib/schema/education.schema.ts`
  - [x] 5.6 Create `apps/web/src/app/api/certifications/route.ts` and `[id]/route.ts` with CRUD handlers
  - [x] 5.7 Create `apps/web/src/app/api/certifications/_lib/schema/certification.schema.ts`

- [x] 6. Experiences & Achievements Routes

  - [x] 6.1 Create `apps/web/src/app/api/experiences/route.ts` with GET (list by user_id) and POST handlers
  - [x] 6.2 Create `apps/web/src/app/api/experiences/[id]/route.ts` with GET, PATCH, DELETE handlers
  - [x] 6.3 Create `apps/web/src/app/api/experiences/_lib/schema/experience.schema.ts` with Zod schemas (including skills array)
  - [x] 6.4 Create `apps/web/src/app/api/achievements/route.ts` with GET (list by experience_id) and POST handlers
  - [x] 6.5 Create `apps/web/src/app/api/achievements/[id]/route.ts` with GET, PATCH, DELETE handlers
  - [x] 6.6 Create `apps/web/src/app/api/achievements/_lib/schema/achievement.schema.ts`

- [x] 7. Jobs Routes (CRUD)

  - [x] 7.1 Create `apps/web/src/app/api/jobs/route.ts` with GET (list with filters: user_id, status_filter, favorite_only, pagination) and POST handlers
  - [x] 7.2 Create `apps/web/src/app/api/jobs/[id]/route.ts` with GET (extended response), PATCH, DELETE handlers
  - [x] 7.3 Create `apps/web/src/app/api/jobs/_lib/schema/job.schema.ts` with JobCreate, JobUpdate schemas
  - [x] 7.4 Implement query param parsing for status filter, favorite_only, skip, limit
  - [x] 7.5 Return extended job response including has_resume, has_cover_letter flags

- [x] 8. Jobs Routes (Non-Standard Endpoints)

  - [x] 8.1 Create `apps/web/src/app/api/jobs/bulk-delete/route.ts` with DELETE handler accepting job_ids array
  - [x] 8.2 Create `apps/web/src/app/api/jobs/[id]/favorite/route.ts` with PATCH handler for toggle favorite
  - [x] 8.3 Create `apps/web/src/app/api/jobs/[id]/status/route.ts` with PATCH handler for status update
  - [x] 8.4 Create `apps/web/src/app/api/jobs/[id]/apply/route.ts` with POST handler setting applied_at timestamp
  - [x] 8.5 Create shared utility for job existence validation in `_lib/server/`

- [x] 9. Job Intake System Routes

  - [x] 9.1 Create `apps/web/src/app/api/jobs/[id]/intake-session/route.ts` with GET, POST, PATCH handlers
  - [x] 9.2 Create `apps/web/src/app/api/jobs/[id]/intake-session/[sessionId]/messages/route.ts` with GET, POST handlers
  - [x] 9.3 Create `apps/web/src/app/api/experience-proposals/route.ts` with GET (list by session_id) and POST handlers
  - [x] 9.4 Create `apps/web/src/app/api/experience-proposals/[id]/route.ts` with GET, PATCH, DELETE handlers
  - [x] 9.5 Create Zod schemas for intake session and experience proposal validation
  - [x] 9.6 Handle JSONB fields for messages array and proposed_content

- [x] 10. Resumes & Cover Letters Routes

  - [x] 10.1 Create `apps/web/src/app/api/resumes/route.ts` with GET and POST (by job_id) handlers
  - [x] 10.2 Create `apps/web/src/app/api/resumes/[id]/route.ts` with GET, PATCH, DELETE handlers
  - [x] 10.3 Create `apps/web/src/app/api/resumes/[id]/versions/route.ts` for resume version history
  - [x] 10.4 Create `apps/web/src/app/api/cover-letters/route.ts` with GET and POST (by job_id) handlers
  - [x] 10.5 Create `apps/web/src/app/api/cover-letters/[id]/route.ts` with GET, PATCH, DELETE handlers
  - [x] 10.6 Create `apps/web/src/app/api/cover-letters/[id]/versions/route.ts` for cover letter version history
  - [x] 10.7 Create Zod schemas for resumes and cover letters with JSONB content validation

- [x] 11. Supporting Entities Routes

  - [x] 11.1 Create `apps/web/src/app/api/messages/route.ts` and `[id]/route.ts` with CRUD handlers
  - [x] 11.2 Create `apps/web/src/app/api/responses/route.ts` with GET (list with source/ignore filters) and POST handlers
  - [x] 11.3 Create `apps/web/src/app/api/responses/[id]/route.ts` with GET, PATCH, DELETE handlers
  - [x] 11.4 Create `apps/web/src/app/api/notes/route.ts` and `[id]/route.ts` with CRUD handlers
  - [x] 11.5 Create `apps/web/src/app/api/templates/route.ts` with GET (list) and POST handlers
  - [x] 11.6 Create `apps/web/src/app/api/templates/[id]/route.ts` with GET, PATCH, DELETE handlers
  - [x] 11.7 Migrate template HTML files from `apps/api/src/features/*/templates/` to database using seed script

- [x] 12. Frontend Integration & Cleanup
  - [x] 12.1 Update `apps/web/src/lib/api/client.ts` to use `/api/` base URL instead of `http://localhost:8000/api/v1/`
  - [x] 12.2 Update all files in `apps/web/src/lib/api/` (jobs.ts, experiences.ts, etc.) to use new route paths
  - [x] 12.3 Update type imports from `@/types/api` to `@resume/database/types` throughout codebase
  - [x] 12.4 Refactor `/api/chat/` routes to use `getSupabaseServerClient()` for any persistence
  - [x] 12.5 Refactor `/api/workflows/` routes to use Supabase instead of calling Python API
  - [x] 12.6 Delete `apps/web/src/types/api.ts` (OpenAPI-generated types)
  - [x] 12.7 Remove `openapi-typescript` from `apps/web/package.json` and related scripts
  - [ ] 12.8 Delete `/apps/api/` directory after verifying all functionality works
