/**
 * Resumes API - List and Create (Versions-based)
 *
 * GET  /api/resumes?job_id=1 - Get pinned resume versions (optionally filter by job_id)
 * POST /api/resumes - Create a new resume version
 *
 * Note: The resumes table has been consolidated into resume_versions.
 * The "current" resume for a job is the version with is_pinned=true.
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { resumeVersionCreateSchema } from "./_lib/schema/resume.schema";

/**
 * GET /api/resumes
 * List pinned resume versions, optionally filtered by job_id.
 * Returns versions with is_pinned=true (the "current" resume for each job).
 *
 * Query Parameters:
 * - job_id (optional): Filter by job ID
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const jobIdParam = searchParams.get("job_id");

    const supabase = await getSupabaseServerClient();

    let query = supabase
      .from("resume_versions")
      .select("*")
      .eq("is_pinned", true)
      .order("created_at", { ascending: false });

    // Apply job_id filter if provided
    if (jobIdParam) {
      const jobId = parseInt(jobIdParam, 10);
      if (isNaN(jobId)) {
        return NextResponse.json(
          { error: "Invalid job_id parameter" },
          { status: 400 }
        );
      }
      query = query.eq("job_id", jobId);
    }

    const { data: resumes, error } = await query;

    if (error) {
      console.error("Failed to list resumes:", error);
      return NextResponse.json(
        { error: "Failed to list resumes", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(resumes);
  } catch (error) {
    console.error("Unexpected error listing resumes:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/resumes
 * Create a new resume version.
 * If is_pinned is true, will unpin any existing pinned version for the job.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = resumeVersionCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Verify job exists
    const { data: job, error: jobError } = await supabase
      .from("jobs")
      .select("id")
      .eq("id", parseResult.data.job_id)
      .single();

    if (jobError || !job) {
      return NextResponse.json(
        { error: "Job not found" },
        { status: 404 }
      );
    }

    // Get the current highest version_index for this job
    const { data: latestVersion } = await supabase
      .from("resume_versions")
      .select("version_index")
      .eq("job_id", parseResult.data.job_id)
      .order("version_index", { ascending: false })
      .limit(1)
      .single();

    const nextVersionIndex = (latestVersion?.version_index ?? 0) + 1;

    // If this version should be pinned, unpin any existing pinned version
    if (parseResult.data.is_pinned) {
      await supabase
        .from("resume_versions")
        .update({ is_pinned: false })
        .eq("job_id", parseResult.data.job_id)
        .eq("is_pinned", true);
    }

    const { data: version, error } = await supabase
      .from("resume_versions")
      .insert({
        job_id: parseResult.data.job_id,
        resume_json: parseResult.data.resume_json,
        template_name: parseResult.data.template_name,
        event_type: parseResult.data.event_type,
        parent_version_id: parseResult.data.parent_version_id ?? null,
        created_by_user_id: parseResult.data.created_by_user_id,
        version_index: nextVersionIndex,
        is_pinned: parseResult.data.is_pinned ?? false,
        locked: false,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create resume version:", error);
      return NextResponse.json(
        { error: "Failed to create resume version", details: error.message },
        { status: 500 }
      );
    }

    // Update job's has_resume flag if this is the first version or if pinned
    if (nextVersionIndex === 1 || parseResult.data.is_pinned) {
      await supabase
        .from("jobs")
        .update({ has_resume: true })
        .eq("id", parseResult.data.job_id);
    }

    return NextResponse.json(version, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating resume version:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
