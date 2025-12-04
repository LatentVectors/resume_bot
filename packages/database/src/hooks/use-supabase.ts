/**
 * React hook for accessing Supabase client in client components.
 *
 * Usage:
 *   "use client";
 *   import { useSupabase } from "@resume/database/hooks";
 *
 *   export function MyComponent() {
 *     const supabase = useSupabase();
 *     // Use supabase client...
 *   }
 */

"use client";

import { useMemo } from "react";
import { createBrowserClient } from "../client";

/**
 * React hook that returns a memoized Supabase browser client.
 * Use this in client components to access the database.
 */
export function useSupabase() {
  const supabase = useMemo(() => createBrowserClient(), []);
  return supabase;
}

