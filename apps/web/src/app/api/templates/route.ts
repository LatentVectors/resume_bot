/**
 * Templates API - List and Create
 *
 * GET  /api/templates?type=resume - List templates with optional type filter
 * POST /api/templates - Create a new template
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import type { TemplateType } from "@resume/database/types";
import {
  templateCreateSchema,
  templateTypeValues,
} from "./_lib/schema/template.schema";

/**
 * GET /api/templates
 * List templates with optional type filter.
 *
 * Query Parameters:
 * - type (optional): Filter by template type ("resume" or "cover_letter")
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;

    // Parse type filter (optional)
    const typeFilter = searchParams.get("type") as TemplateType | null;
    if (
      typeFilter &&
      !templateTypeValues.includes(
        typeFilter as (typeof templateTypeValues)[number]
      )
    ) {
      return NextResponse.json(
        {
          error: `Invalid type filter. Must be one of: ${templateTypeValues.join(", ")}`,
        },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Build the query
    let query = supabase.from("templates").select("*");

    // Apply type filter if provided
    if (typeFilter) {
      query = query.eq("type", typeFilter);
    }

    // Order by name
    query = query.order("name", { ascending: true });

    const { data: templates, error } = await query;

    if (error) {
      console.error("Failed to list templates:", error);
      return NextResponse.json(
        { error: "Failed to list templates", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(templates);
  } catch (error) {
    console.error("Unexpected error listing templates:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/templates
 * Create a new template.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = templateCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Check if template with same name already exists
    const { data: existingTemplate } = await supabase
      .from("templates")
      .select("id")
      .eq("name", parseResult.data.name)
      .single();

    if (existingTemplate) {
      return NextResponse.json(
        { error: "Template with this name already exists" },
        { status: 409 }
      );
    }

    const { data: template, error } = await supabase
      .from("templates")
      .insert({
        name: parseResult.data.name,
        type: parseResult.data.type,
        html_content: parseResult.data.html_content,
        description: parseResult.data.description ?? null,
        preview_image_url: parseResult.data.preview_image_url ?? null,
        is_default: parseResult.data.is_default ?? false,
        metadata: parseResult.data.metadata ?? {},
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create template:", error);
      return NextResponse.json(
        { error: "Failed to create template", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(template, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating template:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

