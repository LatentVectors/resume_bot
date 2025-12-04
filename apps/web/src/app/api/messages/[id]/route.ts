/**
 * Messages API - Single Message Operations
 *
 * GET    /api/messages/[id] - Get a message by ID
 * PATCH  /api/messages/[id] - Update a message
 * DELETE /api/messages/[id] - Delete a message
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { messageUpdateSchema } from "../_lib/schema/message.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/messages/[id]
 * Get a message by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const messageId = parseInt(id, 10);

    if (isNaN(messageId)) {
      return NextResponse.json({ error: "Invalid message ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    const { data: message, error } = await supabase
      .from("messages")
      .select("*")
      .eq("id", messageId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json({ error: "Message not found" }, { status: 404 });
      }
      console.error("Failed to get message:", error);
      return NextResponse.json(
        { error: "Failed to get message", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(message);
  } catch (error) {
    console.error("Unexpected error getting message:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/messages/[id]
 * Update a message.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const messageId = parseInt(id, 10);

    if (isNaN(messageId)) {
      return NextResponse.json({ error: "Invalid message ID" }, { status: 400 });
    }

    const body = await req.json();

    // Validate request body
    const parseResult = messageUpdateSchema.safeParse(body);
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
    if (updates.channel !== undefined) updateData.channel = updates.channel;
    if (updates.body !== undefined) updateData.body = updates.body;
    if (updates.sent_at !== undefined) updateData.sent_at = updates.sent_at;

    const { data: message, error } = await supabase
      .from("messages")
      .update(updateData)
      .eq("id", messageId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json({ error: "Message not found" }, { status: 404 });
      }
      console.error("Failed to update message:", error);
      return NextResponse.json(
        { error: "Failed to update message", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(message);
  } catch (error) {
    console.error("Unexpected error updating message:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/messages/[id]
 * Delete a message.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const messageId = parseInt(id, 10);

    if (isNaN(messageId)) {
      return NextResponse.json({ error: "Invalid message ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    // First check if message exists
    const { data: existingMessage, error: fetchError } = await supabase
      .from("messages")
      .select("id")
      .eq("id", messageId)
      .single();

    if (fetchError || !existingMessage) {
      return NextResponse.json({ error: "Message not found" }, { status: 404 });
    }

    const { error } = await supabase.from("messages").delete().eq("id", messageId);

    if (error) {
      console.error("Failed to delete message:", error);
      return NextResponse.json(
        { error: "Failed to delete message", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting message:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

