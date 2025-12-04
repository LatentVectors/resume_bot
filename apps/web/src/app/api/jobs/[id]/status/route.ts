/**
 * Jobs API - Status Update
 *
 * PATCH /api/jobs/[id]/status - Update job status
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { validateJobExists } from "../../_lib/server/job-utils";
import { jobStatusEnum } from "../../_lib/schema/job.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * PATCH /api/jobs/[id]/status
 * Update job status.
 *
 * Query params: ?status=Saved|Applied|Interviewing|Not Selected|No Offer|Hired
 * Response: Updated job object
 *
 * Note: Transitioning to "Applied" status for the first time will set the applied_at timestamp.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;

    // Get status value from query params (matching Python API pattern)
    const searchParams = req.nextUrl.searchParams;
    const statusParam = searchParams.get("status");

    if (statusParam === null) {
      return NextResponse.json(
        { error: "status query parameter is required" },
        { status: 400 }
      );
    }

    // Validate status value
    const statusResult = jobStatusEnum.safeParse(statusParam);
    if (!statusResult.success) {
      return NextResponse.json(
        {
          error: "Invalid status value",
          details: `Status must be one of: ${jobStatusEnum.options.join(", ")}`,
        },
        { status: 400 }
      );
    }

    const newStatus = statusResult.data;

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
      status: typeof newStatus;
      applied_at?: string;
    } = { status: newStatus };

    // Set applied_at on first transition to "Applied"
    if (newStatus === "Applied" && currentJob.applied_at === null) {
      updateData.applied_at = new Date().toISOString();
    }

    // Update status
    const { data: job, error } = await supabase
      .from("jobs")
      .update(updateData)
      .eq("id", currentJob.id)
      .select()
      .single();

    if (error) {
      console.error("Failed to update job status:", error);
      return NextResponse.json(
        { error: "Failed to update job status", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(job);
  } catch (error) {
    console.error("Unexpected error updating status:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

