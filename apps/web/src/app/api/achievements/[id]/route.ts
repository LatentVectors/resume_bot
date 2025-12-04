/**
 * Achievements API - Single Achievement Operations
 *
 * GET    /api/achievements/[id] - Get an achievement by ID
 * PATCH  /api/achievements/[id] - Update an achievement
 * DELETE /api/achievements/[id] - Delete an achievement
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { achievementUpdateSchema } from "../_lib/schema/achievement.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/achievements/[id]
 * Get an achievement by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const achievementId = parseInt(id, 10);

    if (isNaN(achievementId)) {
      return NextResponse.json(
        { error: "Invalid achievement ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: achievement, error } = await supabase
      .from("achievements")
      .select("*")
      .eq("id", achievementId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Achievement not found" },
          { status: 404 }
        );
      }
      console.error("Failed to get achievement:", error);
      return NextResponse.json(
        { error: "Failed to get achievement", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(achievement);
  } catch (error) {
    console.error("Unexpected error getting achievement:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/achievements/[id]
 * Update an achievement.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const achievementId = parseInt(id, 10);

    if (isNaN(achievementId)) {
      return NextResponse.json(
        { error: "Invalid achievement ID" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = achievementUpdateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    // Check if there are any updates
    if (Object.keys(parseResult.data).length === 0) {
      return NextResponse.json(
        { error: "No fields to update" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: achievement, error } = await supabase
      .from("achievements")
      .update(parseResult.data)
      .eq("id", achievementId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Achievement not found" },
          { status: 404 }
        );
      }
      console.error("Failed to update achievement:", error);
      return NextResponse.json(
        { error: "Failed to update achievement", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(achievement);
  } catch (error) {
    console.error("Unexpected error updating achievement:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/achievements/[id]
 * Delete an achievement.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const achievementId = parseInt(id, 10);

    if (isNaN(achievementId)) {
      return NextResponse.json(
        { error: "Invalid achievement ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // First check if achievement exists
    const { data: existingAchievement, error: fetchError } = await supabase
      .from("achievements")
      .select("id")
      .eq("id", achievementId)
      .single();

    if (fetchError || !existingAchievement) {
      return NextResponse.json(
        { error: "Achievement not found" },
        { status: 404 }
      );
    }

    // Delete the achievement
    const { error } = await supabase
      .from("achievements")
      .delete()
      .eq("id", achievementId);

    if (error) {
      console.error("Failed to delete achievement:", error);
      return NextResponse.json(
        { error: "Failed to delete achievement", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting achievement:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

