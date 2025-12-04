# @resume/database

Supabase PostgreSQL database client and types for the Resume application.

## Setup

### Prerequisites

- [Supabase CLI](https://supabase.com/docs/guides/cli) installed
- Docker running (for local Supabase)

### Installation

```bash
# From monorepo root
npm install

# Start local Supabase
cd packages/database
npx supabase start
```

### Environment Variables

Add to `apps/web/.env.local`:

```bash
# Supabase Configuration (get from `supabase start` output)
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key-from-supabase-start>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key-from-supabase-start>

# User Context (temporary, until Supabase Auth)
CURRENT_USER_ID=1
```

## Usage

### Server Components / Server Actions / Route Handlers

```typescript
import { getSupabaseServerClient } from "@resume/database/server";

export async function myServerAction() {
  const supabase = await getSupabaseServerClient();
  const { data, error } = await supabase.from("jobs").select("*");
}
```

### Client Components

```typescript
"use client";
import { useSupabase } from "@resume/database/hooks";

export function MyComponent() {
  const supabase = useSupabase();
  // Use supabase client...
}
```

### Admin Operations (bypass RLS)

```typescript
import { getSupabaseServerAdminClient } from "@resume/database/admin";

export async function adminOperation() {
  const supabase = getSupabaseServerAdminClient();
  // This bypasses RLS policies - use with caution
}
```

### Types

```typescript
import type { Job, JobInsert, JobUpdate, Experience } from "@resume/database/types";
```

## Database Commands

```bash
# Start local Supabase
npm run db:start

# Stop local Supabase
npm run db:stop

# Reset database (runs migrations + seed)
npm run db:reset

# Generate TypeScript types from schema
npm run db:gen-types
```

## Data Migration

Migrate data from existing SQLite database:

```bash
# Set environment variables
export SQLITE_DATABASE_PATH=../../apps/api/data/resume.db
export NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
export SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>

# Run migration
npm run migrate:from-sqlite
```

## Local Development URLs

After running `supabase start`:

- **Supabase Studio**: http://localhost:54323
- **API URL**: http://localhost:54321
- **Database URL**: postgresql://postgres:postgres@localhost:54322/postgres

