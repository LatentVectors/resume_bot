/**
 * Cover Letters API - List and Create (Versions-based)
 *
 * GET  /api/cover-letters?job_id=1 - Get pinned cover letter versions (optionally filter by job_id)
 * POST /api/cover-letters - Create a new cover letter version
 *
 * Note: The cover_letters table has been consolidated into cover_letter_versions.
 * The "current" cover letter for a job is the version with is_pinned=true.
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { coverLetterVersionCreateSchema } from "./_lib/schema/cover-letter.schema";

/**
 * GET /api/cover-letters
 * List pinned cover letter versions, optionally filtered by job_id.
 * Returns versions with is_pinned=true (the "current" cover letter for each job).
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
      .from("cover_letter_versions")
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

    const { data: coverLetters, error } = await query;

    if (error) {
      console.error("Failed to list cover letters:", error);
      return NextResponse.json(
        { error: "Failed to list cover letters", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(coverLetters);
  } catch (error) {
    console.error("Unexpected error listing cover letters:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/cover-letters
 * Create a new cover letter version.
 * If is_pinned is true, will unpin any existing pinned version for the job.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = coverLetterVersionCreateSchema.safeParse(body);
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
      .from("cover_letter_versions")
      .select("version_index")
      .eq("job_id", parseResult.data.job_id)
      .order("version_index", { ascending: false })
      .limit(1)
      .single();

    const nextVersionIndex = (latestVersion?.version_index ?? 0) + 1;

    // If this version should be pinned, unpin any existing pinned version
    if (parseResult.data.is_pinned) {
      await supabase
        .from("cover_letter_versions")
        .update({ is_pinned: false })
        .eq("job_id", parseResult.data.job_id)
        .eq("is_pinned", true);
    }

    const { data: version, error } = await supabase
      .from("cover_letter_versions")
      .insert({
        job_id: parseResult.data.job_id,
        cover_letter_json: parseResult.data.cover_letter_json,
        template_name: parseResult.data.template_name ?? "cover_000.html",
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
      console.error("Failed to create cover letter version:", error);
      return NextResponse.json(
        { error: "Failed to create cover letter version", details: error.message },
        { status: 500 }
      );
    }

    // Update job's has_cover_letter flag if this is the first version or if pinned
    if (nextVersionIndex === 1 || parseResult.data.is_pinned) {
      await supabase
        .from("jobs")
        .update({ has_cover_letter: true })
        .eq("id", parseResult.data.job_id);
    }

    return NextResponse.json(version, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating cover letter version:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
