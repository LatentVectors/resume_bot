/**
 * Cover Letter Versions API - Single Version Operations
 *
 * GET    /api/cover-letters/[id] - Get a cover letter version by ID
 * PATCH  /api/cover-letters/[id] - Update a cover letter version (including pinning)
 * DELETE /api/cover-letters/[id] - Delete a cover letter version
 *
 * Note: The cover_letters table has been consolidated into cover_letter_versions.
 * The [id] parameter refers to a version ID.
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { coverLetterVersionUpdateSchema } from "../_lib/schema/cover-letter.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/cover-letters/[id]
 * Get a cover letter version by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const versionId = parseInt(id, 10);

    if (isNaN(versionId)) {
      return NextResponse.json({ error: "Invalid version ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    const { data: version, error } = await supabase
      .from("cover_letter_versions")
      .select("*")
      .eq("id", versionId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json({ error: "Cover letter version not found" }, { status: 404 });
      }
      console.error("Failed to get cover letter version:", error);
      return NextResponse.json(
        { error: "Failed to get cover letter version", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(version);
  } catch (error) {
    console.error("Unexpected error getting cover letter version:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/cover-letters/[id]
 * Update a cover letter version.
 * If is_pinned is set to true, will unpin any existing pinned version for the job.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const versionId = parseInt(id, 10);

    if (isNaN(versionId)) {
      return NextResponse.json({ error: "Invalid version ID" }, { status: 400 });
    }

    const body = await req.json();

    // Validate request body
    const parseResult = coverLetterVersionUpdateSchema.safeParse(body);
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

    // Get the current version to find its job_id
    const { data: currentVersion, error: fetchError } = await supabase
      .from("cover_letter_versions")
      .select("id, job_id, is_pinned")
      .eq("id", versionId)
      .single();

    if (fetchError || !currentVersion) {
      return NextResponse.json({ error: "Cover letter version not found" }, { status: 404 });
    }

    // If setting is_pinned to true, unpin any existing pinned version for this job
    if (updates.is_pinned === true && !currentVersion.is_pinned) {
      await supabase
        .from("cover_letter_versions")
        .update({ is_pinned: false })
        .eq("job_id", currentVersion.job_id)
        .eq("is_pinned", true);
    }

    // Build update object, only including defined fields
    const updateData: Record<string, unknown> = {};
    if (updates.cover_letter_json !== undefined) updateData.cover_letter_json = updates.cover_letter_json;
    if (updates.template_name !== undefined) updateData.template_name = updates.template_name;
    if (updates.is_pinned !== undefined) updateData.is_pinned = updates.is_pinned;
    if (updates.locked !== undefined) updateData.locked = updates.locked;

    const { data: version, error } = await supabase
      .from("cover_letter_versions")
      .update(updateData)
      .eq("id", versionId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json({ error: "Cover letter version not found" }, { status: 404 });
      }
      console.error("Failed to update cover letter version:", error);
      return NextResponse.json(
        { error: "Failed to update cover letter version", details: error.message },
        { status: 500 }
      );
    }

    // Update job's has_cover_letter flag if we just pinned this version
    if (updates.is_pinned === true) {
      await supabase
        .from("jobs")
        .update({ has_cover_letter: true })
        .eq("id", currentVersion.job_id);
    }

    return NextResponse.json(version);
  } catch (error) {
    console.error("Unexpected error updating cover letter version:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/cover-letters/[id]
 * Delete a cover letter version.
 * If deleting the pinned version, will unset has_cover_letter on the job.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const versionId = parseInt(id, 10);

    if (isNaN(versionId)) {
      return NextResponse.json({ error: "Invalid version ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    // First get the version to find the job_id and check if pinned
    const { data: existingVersion, error: fetchError } = await supabase
      .from("cover_letter_versions")
      .select("id, job_id, is_pinned")
      .eq("id", versionId)
      .single();

    if (fetchError || !existingVersion) {
      return NextResponse.json({ error: "Cover letter version not found" }, { status: 404 });
    }

    // Delete the version
    const { error } = await supabase
      .from("cover_letter_versions")
      .delete()
      .eq("id", versionId);

    if (error) {
      console.error("Failed to delete cover letter version:", error);
      return NextResponse.json(
        { error: "Failed to delete cover letter version", details: error.message },
        { status: 500 }
      );
    }

    // If we deleted the pinned version, check if there are other versions
    if (existingVersion.is_pinned) {
      const { data: remainingVersions } = await supabase
        .from("cover_letter_versions")
        .select("id")
        .eq("job_id", existingVersion.job_id)
        .limit(1);

      // If no versions remain, update job's has_cover_letter flag
      if (!remainingVersions || remainingVersions.length === 0) {
        await supabase
          .from("jobs")
          .update({ has_cover_letter: false })
          .eq("id", existingVersion.job_id);
      }
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting cover letter version:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
