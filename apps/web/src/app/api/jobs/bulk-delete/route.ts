/**
 * Jobs API - Bulk Delete
 *
 * DELETE /api/jobs/bulk-delete - Delete multiple jobs in a single operation
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { bulkDeleteSchema } from "../_lib/schema/job.schema";

/**
 * DELETE /api/jobs/bulk-delete
 * Delete multiple jobs in a single transaction.
 *
 * Request body: { job_ids: number[] }
 * Response: { successful: number, failed: number }
 */
export async function DELETE(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = bulkDeleteSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const { job_ids } = parseResult.data;

    const supabase = await getSupabaseServerClient();

    // First, check which jobs exist
    const { data: existingJobs, error: fetchError } = await supabase
      .from("jobs")
      .select("id")
      .in("id", job_ids);

    if (fetchError) {
      console.error("Failed to fetch jobs for bulk delete:", fetchError);
      return NextResponse.json(
        { error: "Failed to fetch jobs", details: fetchError.message },
        { status: 500 }
      );
    }

    const existingIds = new Set(existingJobs?.map((j) => j.id) ?? []);
    const idsToDelete = job_ids.filter((id) => existingIds.has(id));
    const notFoundCount = job_ids.length - idsToDelete.length;

    if (idsToDelete.length === 0) {
      // None of the requested jobs exist
      return NextResponse.json({
        successful: 0,
        failed: notFoundCount,
      });
    }

    // Delete the jobs that exist
    const { error: deleteError } = await supabase
      .from("jobs")
      .delete()
      .in("id", idsToDelete);

    if (deleteError) {
      console.error("Failed to bulk delete jobs:", deleteError);
      return NextResponse.json(
        { error: "Failed to delete jobs", details: deleteError.message },
        { status: 500 }
      );
    }

    return NextResponse.json({
      successful: idsToDelete.length,
      failed: notFoundCount,
    });
  } catch (error) {
    console.error("Unexpected error during bulk delete:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

