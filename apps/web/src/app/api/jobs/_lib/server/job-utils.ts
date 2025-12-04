/**
 * Shared utility functions for Job API routes.
 *
 * These utilities provide common operations like job existence validation
 * to avoid code duplication across route handlers.
 */

import { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "@resume/database/types";

/**
 * Result of a job validation check.
 */
export type JobValidationResult =
  | { success: true; job: Database["public"]["Tables"]["jobs"]["Row"] }
  | { success: false; error: string; status: 400 | 404 };

/**
 * Validates that a job exists and returns it.
 *
 * @param supabase - The Supabase client instance
 * @param jobId - The job ID to validate (as string from URL params)
 * @returns JobValidationResult indicating success with the job, or failure with error details
 */
export async function validateJobExists(
  supabase: SupabaseClient<Database>,
  jobId: string
): Promise<JobValidationResult> {
  const parsedId = parseInt(jobId, 10);

  if (isNaN(parsedId)) {
    return {
      success: false,
      error: "Invalid job ID",
      status: 400,
    };
  }

  const { data: job, error } = await supabase
    .from("jobs")
    .select("*")
    .eq("id", parsedId)
    .single();

  if (error) {
    if (error.code === "PGRST116") {
      return {
        success: false,
        error: "Job not found",
        status: 404,
      };
    }
    throw error;
  }

  return {
    success: true,
    job,
  };
}

/**
 * Parses and validates a job ID from URL parameters.
 *
 * @param id - The job ID string from URL params
 * @returns The parsed job ID or null if invalid
 */
export function parseJobId(id: string): number | null {
  const parsedId = parseInt(id, 10);
  return isNaN(parsedId) ? null : parsedId;
}

