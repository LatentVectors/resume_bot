/**
 * @resume/database - Supabase database client and types
 *
 * Usage:
 *   import { getSupabaseServerClient } from "@resume/database/server";
 *   import { getSupabaseServerAdminClient } from "@resume/database/admin";
 *   import { createBrowserClient } from "@resume/database/client";
 *   import { useSupabase } from "@resume/database/hooks";
 *   import type { Job, JobInsert } from "@resume/database/types";
 */

// Re-export server client
export { getSupabaseServerClient } from "./server-client";

// Re-export admin client
export { getSupabaseServerAdminClient } from "./admin-client";

// Re-export browser client
export { createBrowserClient } from "./client";

// Re-export types
export * from "./types";

