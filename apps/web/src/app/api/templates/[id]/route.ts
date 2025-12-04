/**
 * Templates API - Single Template Operations
 *
 * GET    /api/templates/[id] - Get a template by ID
 * PATCH  /api/templates/[id] - Update a template
 * DELETE /api/templates/[id] - Delete a template
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { templateUpdateSchema } from "../_lib/schema/template.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/templates/[id]
 * Get a template by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const templateId = parseInt(id, 10);

    if (isNaN(templateId)) {
      return NextResponse.json(
        { error: "Invalid template ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: template, error } = await supabase
      .from("templates")
      .select("*")
      .eq("id", templateId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Template not found" },
          { status: 404 }
        );
      }
      console.error("Failed to get template:", error);
      return NextResponse.json(
        { error: "Failed to get template", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(template);
  } catch (error) {
    console.error("Unexpected error getting template:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/templates/[id]
 * Update a template.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const templateId = parseInt(id, 10);

    if (isNaN(templateId)) {
      return NextResponse.json(
        { error: "Invalid template ID" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = templateUpdateSchema.safeParse(body);
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

    // If name is being updated, check for uniqueness
    if (updates.name) {
      const { data: existingTemplate } = await supabase
        .from("templates")
        .select("id")
        .eq("name", updates.name)
        .neq("id", templateId)
        .single();

      if (existingTemplate) {
        return NextResponse.json(
          { error: "Template with this name already exists" },
          { status: 409 }
        );
      }
    }

    // Build update object, only including defined fields
    const updateData: Record<string, unknown> = {};
    if (updates.name !== undefined) updateData.name = updates.name;
    if (updates.type !== undefined) updateData.type = updates.type;
    if (updates.html_content !== undefined)
      updateData.html_content = updates.html_content;
    if (updates.description !== undefined)
      updateData.description = updates.description;
    if (updates.preview_image_url !== undefined)
      updateData.preview_image_url = updates.preview_image_url;
    if (updates.is_default !== undefined)
      updateData.is_default = updates.is_default;
    if (updates.metadata !== undefined) updateData.metadata = updates.metadata;

    const { data: template, error } = await supabase
      .from("templates")
      .update(updateData)
      .eq("id", templateId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Template not found" },
          { status: 404 }
        );
      }
      console.error("Failed to update template:", error);
      return NextResponse.json(
        { error: "Failed to update template", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(template);
  } catch (error) {
    console.error("Unexpected error updating template:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/templates/[id]
 * Delete a template.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const templateId = parseInt(id, 10);

    if (isNaN(templateId)) {
      return NextResponse.json(
        { error: "Invalid template ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // First check if template exists
    const { data: existingTemplate, error: fetchError } = await supabase
      .from("templates")
      .select("id")
      .eq("id", templateId)
      .single();

    if (fetchError || !existingTemplate) {
      return NextResponse.json(
        { error: "Template not found" },
        { status: 404 }
      );
    }

    const { error } = await supabase
      .from("templates")
      .delete()
      .eq("id", templateId);

    if (error) {
      console.error("Failed to delete template:", error);
      return NextResponse.json(
        { error: "Failed to delete template", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting template:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

