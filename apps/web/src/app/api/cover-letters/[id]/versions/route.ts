/**
 * Cover Letter Versions API - Version History for a Job
 *
 * GET  /api/cover-letters/[id]/versions - List all versions for the job (id is version ID, finds job from it)
 * POST /api/cover-letters/[id]/versions - Create a new version for the job
 *
 * Note: The cover_letters table has been consolidated into cover_letter_versions.
 * The [id] parameter refers to a version ID, used to find the associated job.
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { coverLetterVersionCreateSchema } from "../../_lib/schema/cover-letter.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/cover-letters/[id]/versions
 * List all cover letter versions for the job associated with this version.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const versionId = parseInt(id, 10);

    if (isNaN(versionId)) {
      return NextResponse.json({ error: "Invalid version ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    // Get the version to find its job_id
    const { data: version, error: versionError } = await supabase
      .from("cover_letter_versions")
      .select("job_id")
      .eq("id", versionId)
      .single();

    if (versionError) {
      if (versionError.code === "PGRST116") {
        return NextResponse.json({ error: "Cover letter version not found" }, { status: 404 });
      }
      console.error("Failed to get cover letter version:", versionError);
      return NextResponse.json(
        { error: "Failed to get cover letter version", details: versionError.message },
        { status: 500 }
      );
    }

    // Get all versions for this job
    const { data: versions, error } = await supabase
      .from("cover_letter_versions")
      .select("*")
      .eq("job_id", version.job_id)
      .order("version_index", { ascending: false });

    if (error) {
      console.error("Failed to list cover letter versions:", error);
      return NextResponse.json(
        { error: "Failed to list cover letter versions", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(versions);
  } catch (error) {
    console.error("Unexpected error listing cover letter versions:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/cover-letters/[id]/versions
 * Create a new cover letter version for the job associated with this version.
 */
export async function POST(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const versionId = parseInt(id, 10);

    if (isNaN(versionId)) {
      return NextResponse.json({ error: "Invalid version ID" }, { status: 400 });
    }

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

    // Get the version to verify it exists and get job_id
    const { data: existingVersion, error: versionError } = await supabase
      .from("cover_letter_versions")
      .select("job_id")
      .eq("id", versionId)
      .single();

    if (versionError) {
      if (versionError.code === "PGRST116") {
        return NextResponse.json({ error: "Cover letter version not found" }, { status: 404 });
      }
      console.error("Failed to get cover letter version:", versionError);
      return NextResponse.json(
        { error: "Failed to get cover letter version", details: versionError.message },
        { status: 500 }
      );
    }

    // Verify job_id in request matches the version's job_id
    if (parseResult.data.job_id !== existingVersion.job_id) {
      return NextResponse.json(
        { error: "job_id does not match the version's job" },
        { status: 400 }
      );
    }

    // Get the current highest version_index for this job
    const { data: latestVersion } = await supabase
      .from("cover_letter_versions")
      .select("version_index")
      .eq("job_id", existingVersion.job_id)
      .order("version_index", { ascending: false })
      .limit(1)
      .single();

    const nextVersionIndex = (latestVersion?.version_index ?? 0) + 1;

    // If this version should be pinned, unpin any existing pinned version
    if (parseResult.data.is_pinned) {
      await supabase
        .from("cover_letter_versions")
        .update({ is_pinned: false })
        .eq("job_id", existingVersion.job_id)
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

    return NextResponse.json(version, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating cover letter version:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
