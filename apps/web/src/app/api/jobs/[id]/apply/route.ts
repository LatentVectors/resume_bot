/**
 * Jobs API - Mark as Applied
 *
 * POST /api/jobs/[id]/apply - Mark a job as applied
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { validateJobExists } from "../../_lib/server/job-utils";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * POST /api/jobs/[id]/apply
 * Mark a job as applied.
 *
 * This is a convenience endpoint that:
 * 1. Sets status to "Applied"
 * 2. Sets applied_at timestamp (if not already set)
 *
 * Response: Updated job object
 */
export async function POST(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;

    const supabase = await getSupabaseServerClient();

    // Validate job exists
    const validation = await validateJobExists(supabase, id);
    if (!validation.success) {
      return NextResponse.json(
        { error: validation.error },
        { status: validation.status }
      );
    }

    const currentJob = validation.job;

    // Build update object
    const updateData: {
      status: "Applied";
      applied_at?: string;
    } = { status: "Applied" };

    // Only set applied_at if not already set (preserve first application timestamp)
    if (currentJob.applied_at === null) {
      updateData.applied_at = new Date().toISOString();
    }

    // Update job
    const { data: job, error } = await supabase
      .from("jobs")
      .update(updateData)
      .eq("id", currentJob.id)
      .select()
      .single();

    if (error) {
      console.error("Failed to mark job as applied:", error);
      return NextResponse.json(
        { error: "Failed to mark job as applied", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(job);
  } catch (error) {
    console.error("Unexpected error marking job as applied:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

