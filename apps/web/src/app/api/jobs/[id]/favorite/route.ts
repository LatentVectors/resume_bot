/**
 * Jobs API - Favorite Toggle
 *
 * PATCH /api/jobs/[id]/favorite - Toggle favorite status for a job
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { validateJobExists } from "../../_lib/server/job-utils";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * PATCH /api/jobs/[id]/favorite
 * Toggle favorite status for a job.
 *
 * Query params: ?favorite=true|false
 * Response: Updated job object
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;

    // Get favorite value from query params (matching Python API pattern)
    const searchParams = req.nextUrl.searchParams;
    const favoriteParam = searchParams.get("favorite");

    if (favoriteParam === null) {
      return NextResponse.json(
        { error: "favorite query parameter is required" },
        { status: 400 }
      );
    }

    // Parse boolean from query param
    const favorite = favoriteParam.toLowerCase() === "true";

    const supabase = await getSupabaseServerClient();

    // Validate job exists
    const validation = await validateJobExists(supabase, id);
    if (!validation.success) {
      return NextResponse.json(
        { error: validation.error },
        { status: validation.status }
      );
    }

    // Update favorite status
    const { data: job, error } = await supabase
      .from("jobs")
      .update({ is_favorite: favorite })
      .eq("id", validation.job.id)
      .select()
      .single();

    if (error) {
      console.error("Failed to update favorite status:", error);
      return NextResponse.json(
        { error: "Failed to update favorite status", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(job);
  } catch (error) {
    console.error("Unexpected error toggling favorite:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

