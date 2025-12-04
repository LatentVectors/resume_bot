/**
 * Education API - Single Education Operations
 *
 * GET    /api/education/[id] - Get an education entry by ID
 * PATCH  /api/education/[id] - Update an education entry
 * DELETE /api/education/[id] - Delete an education entry
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { educationUpdateSchema } from "../_lib/schema/education.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/education/[id]
 * Get an education entry by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const educationId = parseInt(id, 10);

    if (isNaN(educationId)) {
      return NextResponse.json(
        { error: "Invalid education ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: education, error } = await supabase
      .from("education")
      .select("*")
      .eq("id", educationId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Education not found" },
          { status: 404 }
        );
      }
      console.error("Failed to get education:", error);
      return NextResponse.json(
        { error: "Failed to get education", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(education);
  } catch (error) {
    console.error("Unexpected error getting education:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/education/[id]
 * Update an education entry.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const educationId = parseInt(id, 10);

    if (isNaN(educationId)) {
      return NextResponse.json(
        { error: "Invalid education ID" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = educationUpdateSchema.safeParse(body);
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

    const { data: education, error } = await supabase
      .from("education")
      .update(parseResult.data)
      .eq("id", educationId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Education not found" },
          { status: 404 }
        );
      }
      console.error("Failed to update education:", error);
      return NextResponse.json(
        { error: "Failed to update education", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(education);
  } catch (error) {
    console.error("Unexpected error updating education:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/education/[id]
 * Delete an education entry.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const educationId = parseInt(id, 10);

    if (isNaN(educationId)) {
      return NextResponse.json(
        { error: "Invalid education ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // First check if education exists
    const { data: existingEducation, error: fetchError } = await supabase
      .from("education")
      .select("id")
      .eq("id", educationId)
      .single();

    if (fetchError || !existingEducation) {
      return NextResponse.json(
        { error: "Education not found" },
        { status: 404 }
      );
    }

    // Delete the education entry
    const { error } = await supabase
      .from("education")
      .delete()
      .eq("id", educationId);

    if (error) {
      console.error("Failed to delete education:", error);
      return NextResponse.json(
        { error: "Failed to delete education", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting education:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

