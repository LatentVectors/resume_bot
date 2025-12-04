/**
 * Notes API - Single Note Operations
 *
 * GET    /api/notes/[id] - Get a note by ID
 * PATCH  /api/notes/[id] - Update a note
 * DELETE /api/notes/[id] - Delete a note
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { noteUpdateSchema } from "../_lib/schema/note.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/notes/[id]
 * Get a note by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const noteId = parseInt(id, 10);

    if (isNaN(noteId)) {
      return NextResponse.json({ error: "Invalid note ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    const { data: note, error } = await supabase
      .from("notes")
      .select("*")
      .eq("id", noteId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json({ error: "Note not found" }, { status: 404 });
      }
      console.error("Failed to get note:", error);
      return NextResponse.json(
        { error: "Failed to get note", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(note);
  } catch (error) {
    console.error("Unexpected error getting note:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/notes/[id]
 * Update a note.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const noteId = parseInt(id, 10);

    if (isNaN(noteId)) {
      return NextResponse.json({ error: "Invalid note ID" }, { status: 400 });
    }

    const body = await req.json();

    // Validate request body
    const parseResult = noteUpdateSchema.safeParse(body);
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

    // Build update object, only including defined fields
    const updateData: Record<string, unknown> = {};
    if (updates.content !== undefined) updateData.content = updates.content;

    const { data: note, error } = await supabase
      .from("notes")
      .update(updateData)
      .eq("id", noteId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json({ error: "Note not found" }, { status: 404 });
      }
      console.error("Failed to update note:", error);
      return NextResponse.json(
        { error: "Failed to update note", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(note);
  } catch (error) {
    console.error("Unexpected error updating note:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/notes/[id]
 * Delete a note.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const noteId = parseInt(id, 10);

    if (isNaN(noteId)) {
      return NextResponse.json({ error: "Invalid note ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    // First check if note exists
    const { data: existingNote, error: fetchError } = await supabase
      .from("notes")
      .select("id")
      .eq("id", noteId)
      .single();

    if (fetchError || !existingNote) {
      return NextResponse.json({ error: "Note not found" }, { status: 404 });
    }

    const { error } = await supabase.from("notes").delete().eq("id", noteId);

    if (error) {
      console.error("Failed to delete note:", error);
      return NextResponse.json(
        { error: "Failed to delete note", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting note:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

