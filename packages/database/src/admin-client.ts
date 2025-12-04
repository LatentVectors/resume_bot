/**
 * Admin Supabase client with elevated privileges.
 * Use sparingly - only when you need to bypass RLS policies.
 *
 * Usage:
 *   import { getSupabaseServerAdminClient } from "@resume/database/admin";
 *
 *   export async function adminOperation() {
 *     const supabase = getSupabaseServerAdminClient();
 *     // This bypasses RLS policies
 *     const { data } = await supabase.from("users").select("*");
 *   }
 */

import { createClient } from "@supabase/supabase-js";
import type { Database } from "./types/database.types";

let adminClient: ReturnType<typeof createClient<Database>> | null = null;

/**
 * Creates a Supabase admin client with service role key.
 * This client bypasses Row Level Security - use with caution.
 */
export function getSupabaseServerAdminClient() {
  if (adminClient) {
    return adminClient;
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseServiceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

  if (!supabaseUrl || !supabaseServiceRoleKey) {
    throw new Error(
      "Missing Supabase environment variables. Set NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."
    );
  }

  adminClient = createClient<Database>(supabaseUrl, supabaseServiceRoleKey, {
    auth: {
      autoRefreshToken: false,
      persistSession: false,
    },
  });

  return adminClient;
}

