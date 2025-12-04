/**
 * Browser Supabase client for client components.
 *
 * Usage in client components:
 *   import { createBrowserClient } from "@resume/database/client";
 *
 *   const supabase = createBrowserClient();
 *   const { data } = await supabase.from("jobs").select("*");
 */

import { createBrowserClient as createSupabaseBrowserClient } from "@supabase/ssr";
import type { Database } from "./types/database.types";

let browserClient: ReturnType<typeof createSupabaseBrowserClient<Database>> | null = null;

/**
 * Creates a Supabase client for browser/client components.
 * Uses singleton pattern to reuse the same client instance.
 */
export function createBrowserClient() {
  if (browserClient) {
    return browserClient;
  }

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

  if (!supabaseUrl || !supabaseAnonKey) {
    throw new Error(
      "Missing Supabase environment variables. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY."
    );
  }

  browserClient = createSupabaseBrowserClient<Database>(supabaseUrl, supabaseAnonKey);

  return browserClient;
}

