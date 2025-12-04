/**
 * Education API - List and Create
 *
 * GET  /api/education?user_id=1 - List all education entries for a user
 * POST /api/education?user_id=1 - Create a new education entry
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { educationCreateSchema } from "./_lib/schema/education.schema";

/**
 * GET /api/education
 * List all education entries for a user.
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

    const { data: educations, error } = await supabase
      .from("education")
      .select("*")
      .eq("user_id", userId)
      .order("grad_date", { ascending: false });

    if (error) {
      console.error("Failed to list education:", error);
      return NextResponse.json(
        { error: "Failed to list education", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(educations);
  } catch (error) {
    console.error("Unexpected error listing education:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/education
 * Create a new education entry.
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
    const parseResult = educationCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: education, error } = await supabase
      .from("education")
      .insert({
        user_id: userId,
        ...parseResult.data,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create education:", error);
      return NextResponse.json(
        { error: "Failed to create education", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(education, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating education:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

