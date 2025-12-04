/**
 * Responses API - Single Response Operations
 *
 * GET    /api/responses/[id] - Get a response by ID
 * PATCH  /api/responses/[id] - Update a response
 * DELETE /api/responses/[id] - Delete a response
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { responseUpdateSchema } from "../_lib/schema/response.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/responses/[id]
 * Get a response by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const responseId = parseInt(id, 10);

    if (isNaN(responseId)) {
      return NextResponse.json(
        { error: "Invalid response ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: response, error } = await supabase
      .from("responses")
      .select("*")
      .eq("id", responseId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Response not found" },
          { status: 404 }
        );
      }
      console.error("Failed to get response:", error);
      return NextResponse.json(
        { error: "Failed to get response", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(response);
  } catch (error) {
    console.error("Unexpected error getting response:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/responses/[id]
 * Update a response.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const responseId = parseInt(id, 10);

    if (isNaN(responseId)) {
      return NextResponse.json(
        { error: "Invalid response ID" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = responseUpdateSchema.safeParse(body);
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

    // If job_id is being updated, verify job exists
    if (updates.job_id) {
      const { data: job, error: jobError } = await supabase
        .from("jobs")
        .select("id")
        .eq("id", updates.job_id)
        .single();

      if (jobError || !job) {
        return NextResponse.json({ error: "Job not found" }, { status: 404 });
      }
    }

    // Build update object, only including defined fields
    const updateData: Record<string, unknown> = {};
    if (updates.job_id !== undefined) updateData.job_id = updates.job_id;
    if (updates.source !== undefined) updateData.source = updates.source;
    if (updates.prompt !== undefined) updateData.prompt = updates.prompt;
    if (updates.response !== undefined) updateData.response = updates.response;
    if (updates.ignore !== undefined) updateData.ignore = updates.ignore;
    if (updates.locked !== undefined) updateData.locked = updates.locked;

    const { data: response, error } = await supabase
      .from("responses")
      .update(updateData)
      .eq("id", responseId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Response not found" },
          { status: 404 }
        );
      }
      console.error("Failed to update response:", error);
      return NextResponse.json(
        { error: "Failed to update response", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(response);
  } catch (error) {
    console.error("Unexpected error updating response:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/responses/[id]
 * Delete a response.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const responseId = parseInt(id, 10);

    if (isNaN(responseId)) {
      return NextResponse.json(
        { error: "Invalid response ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // First check if response exists
    const { data: existingResponse, error: fetchError } = await supabase
      .from("responses")
      .select("id")
      .eq("id", responseId)
      .single();

    if (fetchError || !existingResponse) {
      return NextResponse.json(
        { error: "Response not found" },
        { status: 404 }
      );
    }

    const { error } = await supabase
      .from("responses")
      .delete()
      .eq("id", responseId);

    if (error) {
      console.error("Failed to delete response:", error);
      return NextResponse.json(
        { error: "Failed to delete response", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting response:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

