/**
 * Jobs API - Single Job Operations
 *
 * GET    /api/jobs/[id] - Get a job by ID (extended response)
 * PATCH  /api/jobs/[id] - Update a job
 * DELETE /api/jobs/[id] - Delete a job
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { jobUpdateSchema } from "../_lib/schema/job.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/jobs/[id]
 * Get a job by ID with extended response including has_resume, has_cover_letter.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const jobId = parseInt(id, 10);

    if (isNaN(jobId)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    const { data: job, error } = await supabase
      .from("jobs")
      .select("*")
      .eq("id", jobId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json({ error: "Job not found" }, { status: 404 });
      }
      console.error("Failed to get job:", error);
      return NextResponse.json(
        { error: "Failed to get job", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(job);
  } catch (error) {
    console.error("Unexpected error getting job:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/jobs/[id]
 * Update a job.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const jobId = parseInt(id, 10);

    if (isNaN(jobId)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    const body = await req.json();

    // Validate request body
    const parseResult = jobUpdateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    // Check if there are any updates
    const updates = parseResult.data;
    if (Object.keys(updates).length === 0) {
      return NextResponse.json(
        { error: "No fields to update" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Build update object, only including defined fields
    const updateData: Record<string, unknown> = {};
    if (updates.job_title !== undefined) updateData.job_title = updates.job_title;
    if (updates.company_name !== undefined) updateData.company_name = updates.company_name;
    if (updates.job_description !== undefined) updateData.job_description = updates.job_description;
    if (updates.is_favorite !== undefined) updateData.is_favorite = updates.is_favorite;
    if (updates.status !== undefined) updateData.status = updates.status;
    if (updates.resume_chat_thread_id !== undefined) updateData.resume_chat_thread_id = updates.resume_chat_thread_id;

    // If status is being set to "Applied", check if applied_at should be set
    if (updates.status === "Applied") {
      // Fetch current job to check if applied_at is already set
      const { data: currentJob, error: fetchError } = await supabase
        .from("jobs")
        .select("applied_at")
        .eq("id", jobId)
        .single();

      if (fetchError) {
        if (fetchError.code === "PGRST116") {
          return NextResponse.json({ error: "Job not found" }, { status: 404 });
        }
        throw fetchError;
      }

      // Only set applied_at on first transition to "Applied"
      if (currentJob.applied_at === null) {
        updateData.applied_at = new Date().toISOString();
      }
    }

    const { data: job, error } = await supabase
      .from("jobs")
      .update(updateData)
      .eq("id", jobId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json({ error: "Job not found" }, { status: 404 });
      }
      console.error("Failed to update job:", error);
      return NextResponse.json(
        { error: "Failed to update job", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(job);
  } catch (error) {
    console.error("Unexpected error updating job:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/jobs/[id]
 * Delete a job.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const jobId = parseInt(id, 10);

    if (isNaN(jobId)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    // First check if job exists
    const { data: existingJob, error: fetchError } = await supabase
      .from("jobs")
      .select("id")
      .eq("id", jobId)
      .single();

    if (fetchError || !existingJob) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    // Delete the job (cascading deletes will handle related records)
    const { error } = await supabase.from("jobs").delete().eq("id", jobId);

    if (error) {
      console.error("Failed to delete job:", error);
      return NextResponse.json(
        { error: "Failed to delete job", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting job:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

