/**
 * Experiences API - List and Create
 *
 * GET  /api/experiences?user_id=1 - List all experiences for a user
 * POST /api/experiences?user_id=1 - Create a new experience
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { experienceCreateSchema } from "./_lib/schema/experience.schema";

/**
 * GET /api/experiences
 * List all experiences for a user.
 * Requires user_id query parameter.
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const userIdParam = searchParams.get("user_id");

    if (!userIdParam) {
      return NextResponse.json(
        { error: "user_id query parameter is required" },
        { status: 400 }
      );
    }

    const userId = parseInt(userIdParam, 10);
    if (isNaN(userId)) {
      return NextResponse.json(
        { error: "Invalid user_id parameter" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: experiences, error } = await supabase
      .from("experiences")
      .select("*")
      .eq("user_id", userId)
      .order("start_date", { ascending: false });

    if (error) {
      console.error("Failed to list experiences:", error);
      return NextResponse.json(
        { error: "Failed to list experiences", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(experiences);
  } catch (error) {
    console.error("Unexpected error listing experiences:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/experiences
 * Create a new experience.
 * Requires user_id query parameter.
 */
export async function POST(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const userIdParam = searchParams.get("user_id");

    if (!userIdParam) {
      return NextResponse.json(
        { error: "user_id query parameter is required" },
        { status: 400 }
      );
    }

    const userId = parseInt(userIdParam, 10);
    if (isNaN(userId)) {
      return NextResponse.json(
        { error: "Invalid user_id parameter" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = experienceCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: experience, error } = await supabase
      .from("experiences")
      .insert({
        user_id: userId,
        ...parseResult.data,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create experience:", error);
      return NextResponse.json(
        { error: "Failed to create experience", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(experience, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating experience:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

