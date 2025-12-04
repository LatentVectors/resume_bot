/**
 * Job Intake Session API - Session Operations
 *
 * GET   /api/jobs/[id]/intake-session - Get intake session for a job
 * POST  /api/jobs/[id]/intake-session - Create intake session for a job
 * PATCH /api/jobs/[id]/intake-session - Update intake session for a job
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { intakeSessionUpdateSchema } from "./_lib/schema/intake-session.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/jobs/[id]/intake-session
 * Get intake session for a job.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const jobId = parseInt(id, 10);

    if (isNaN(jobId)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    // First verify the job exists
    const { data: job, error: jobError } = await supabase
      .from("jobs")
      .select("id")
      .eq("id", jobId)
      .single();

    if (jobError || !job) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    // Get the intake session
    const { data: session, error } = await supabase
      .from("job_intake_sessions")
      .select("*")
      .eq("job_id", jobId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Intake session not found" },
          { status: 404 }
        );
      }
      console.error("Failed to get intake session:", error);
      return NextResponse.json(
        { error: "Failed to get intake session", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(session);
  } catch (error) {
    console.error("Unexpected error getting intake session:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/jobs/[id]/intake-session
 * Create intake session for a job.
 */
export async function POST(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const jobId = parseInt(id, 10);

    if (isNaN(jobId)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    // First verify the job exists
    const { data: job, error: jobError } = await supabase
      .from("jobs")
      .select("id")
      .eq("id", jobId)
      .single();

    if (jobError || !job) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    // Check if an intake session already exists
    const { data: existingSession } = await supabase
      .from("job_intake_sessions")
      .select("id")
      .eq("job_id", jobId)
      .single();

    if (existingSession) {
      return NextResponse.json(
        { error: "Intake session already exists for this job" },
        { status: 409 }
      );
    }

    // Create the intake session
    const { data: session, error } = await supabase
      .from("job_intake_sessions")
      .insert({
        job_id: jobId,
        current_step: 1,
        step1_completed: false,
        step2_completed: false,
        step3_completed: false,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create intake session:", error);
      return NextResponse.json(
        { error: "Failed to create intake session", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(session, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating intake session:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/jobs/[id]/intake-session
 * Update intake session for a job.
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
    const parseResult = intakeSessionUpdateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // First verify the job exists
    const { data: job, error: jobError } = await supabase
      .from("jobs")
      .select("id")
      .eq("id", jobId)
      .single();

    if (jobError || !job) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    // Get current intake session
    const { data: existingSession, error: fetchError } = await supabase
      .from("job_intake_sessions")
      .select("*")
      .eq("job_id", jobId)
      .single();

    if (fetchError || !existingSession) {
      return NextResponse.json(
        { error: "Intake session not found" },
        { status: 404 }
      );
    }

    // Build update object
    const updates: Record<string, unknown> = {};
    const { current_step, step_completed, ...otherFields } = parseResult.data;

    // Handle step updates
    if (current_step !== undefined) {
      updates.current_step = current_step;

      // If step_completed matches current_step, mark it as completed
      if (step_completed !== undefined && step_completed === current_step) {
        const stepField = `step${current_step}_completed` as const;
        updates[stepField] = true;
      }
    }

    // Add other fields
    for (const [key, value] of Object.entries(otherFields)) {
      if (value !== undefined) {
        updates[key] = value;
      }
    }

    // Check if there are any updates
    if (Object.keys(updates).length === 0) {
      return NextResponse.json(
        { error: "No fields to update" },
        { status: 400 }
      );
    }

    // Perform the update
    const { data: session, error } = await supabase
      .from("job_intake_sessions")
      .update(updates)
      .eq("job_id", jobId)
      .select()
      .single();

    if (error) {
      console.error("Failed to update intake session:", error);
      return NextResponse.json(
        { error: "Failed to update intake session", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(session);
  } catch (error) {
    console.error("Unexpected error updating intake session:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

