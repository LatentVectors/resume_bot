/**
 * Achievements API - List and Create
 *
 * GET  /api/achievements?experience_id=1 - List all achievements for an experience
 * POST /api/achievements?experience_id=1 - Create a new achievement
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { achievementCreateSchema } from "./_lib/schema/achievement.schema";

/**
 * GET /api/achievements
 * List all achievements for an experience.
 * Requires experience_id query parameter.
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const experienceIdParam = searchParams.get("experience_id");

    if (!experienceIdParam) {
      return NextResponse.json(
        { error: "experience_id query parameter is required" },
        { status: 400 }
      );
    }

    const experienceId = parseInt(experienceIdParam, 10);
    if (isNaN(experienceId)) {
      return NextResponse.json(
        { error: "Invalid experience_id parameter" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: achievements, error } = await supabase
      .from("achievements")
      .select("*")
      .eq("experience_id", experienceId)
      .order("order", { ascending: true });

    if (error) {
      console.error("Failed to list achievements:", error);
      return NextResponse.json(
        { error: "Failed to list achievements", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(achievements);
  } catch (error) {
    console.error("Unexpected error listing achievements:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/achievements
 * Create a new achievement.
 * Requires experience_id query parameter.
 */
export async function POST(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const experienceIdParam = searchParams.get("experience_id");

    if (!experienceIdParam) {
      return NextResponse.json(
        { error: "experience_id query parameter is required" },
        { status: 400 }
      );
    }

    const experienceId = parseInt(experienceIdParam, 10);
    if (isNaN(experienceId)) {
      return NextResponse.json(
        { error: "Invalid experience_id parameter" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = achievementCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Verify the experience exists
    const { data: experience, error: experienceError } = await supabase
      .from("experiences")
      .select("id")
      .eq("id", experienceId)
      .single();

    if (experienceError || !experience) {
      return NextResponse.json(
        { error: "Experience not found" },
        { status: 404 }
      );
    }

    const { data: achievement, error } = await supabase
      .from("achievements")
      .insert({
        experience_id: experienceId,
        ...parseResult.data,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create achievement:", error);
      return NextResponse.json(
        { error: "Failed to create achievement", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(achievement, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating achievement:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

