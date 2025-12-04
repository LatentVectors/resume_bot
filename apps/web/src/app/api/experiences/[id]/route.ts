/**
 * Experiences API - Single Experience Operations
 *
 * GET    /api/experiences/[id] - Get an experience by ID
 * PATCH  /api/experiences/[id] - Update an experience
 * DELETE /api/experiences/[id] - Delete an experience
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { experienceUpdateSchema } from "../_lib/schema/experience.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/experiences/[id]
 * Get an experience by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const experienceId = parseInt(id, 10);

    if (isNaN(experienceId)) {
      return NextResponse.json(
        { error: "Invalid experience ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: experience, error } = await supabase
      .from("experiences")
      .select("*")
      .eq("id", experienceId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Experience not found" },
          { status: 404 }
        );
      }
      console.error("Failed to get experience:", error);
      return NextResponse.json(
        { error: "Failed to get experience", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(experience);
  } catch (error) {
    console.error("Unexpected error getting experience:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/experiences/[id]
 * Update an experience.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const experienceId = parseInt(id, 10);

    if (isNaN(experienceId)) {
      return NextResponse.json(
        { error: "Invalid experience ID" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = experienceUpdateSchema.safeParse(body);
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

    const { data: experience, error } = await supabase
      .from("experiences")
      .update(parseResult.data)
      .eq("id", experienceId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Experience not found" },
          { status: 404 }
        );
      }
      console.error("Failed to update experience:", error);
      return NextResponse.json(
        { error: "Failed to update experience", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(experience);
  } catch (error) {
    console.error("Unexpected error updating experience:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/experiences/[id]
 * Delete an experience.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const experienceId = parseInt(id, 10);

    if (isNaN(experienceId)) {
      return NextResponse.json(
        { error: "Invalid experience ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // First check if experience exists
    const { data: existingExperience, error: fetchError } = await supabase
      .from("experiences")
      .select("id")
      .eq("id", experienceId)
      .single();

    if (fetchError || !existingExperience) {
      return NextResponse.json(
        { error: "Experience not found" },
        { status: 404 }
      );
    }

    // Delete the experience (achievements will cascade delete)
    const { error } = await supabase
      .from("experiences")
      .delete()
      .eq("id", experienceId);

    if (error) {
      console.error("Failed to delete experience:", error);
      return NextResponse.json(
        { error: "Failed to delete experience", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting experience:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

