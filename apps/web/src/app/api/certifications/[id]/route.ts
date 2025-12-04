/**
 * Certifications API - Single Certification Operations
 *
 * GET    /api/certifications/[id] - Get a certification by ID
 * PATCH  /api/certifications/[id] - Update a certification
 * DELETE /api/certifications/[id] - Delete a certification
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { certificationUpdateSchema } from "../_lib/schema/certification.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/certifications/[id]
 * Get a certification by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const certificationId = parseInt(id, 10);

    if (isNaN(certificationId)) {
      return NextResponse.json(
        { error: "Invalid certification ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: certification, error } = await supabase
      .from("certifications")
      .select("*")
      .eq("id", certificationId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Certification not found" },
          { status: 404 }
        );
      }
      console.error("Failed to get certification:", error);
      return NextResponse.json(
        { error: "Failed to get certification", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(certification);
  } catch (error) {
    console.error("Unexpected error getting certification:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/certifications/[id]
 * Update a certification.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const certificationId = parseInt(id, 10);

    if (isNaN(certificationId)) {
      return NextResponse.json(
        { error: "Invalid certification ID" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = certificationUpdateSchema.safeParse(body);
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

    const { data: certification, error } = await supabase
      .from("certifications")
      .update(parseResult.data)
      .eq("id", certificationId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Certification not found" },
          { status: 404 }
        );
      }
      console.error("Failed to update certification:", error);
      return NextResponse.json(
        { error: "Failed to update certification", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(certification);
  } catch (error) {
    console.error("Unexpected error updating certification:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/certifications/[id]
 * Delete a certification.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const certificationId = parseInt(id, 10);

    if (isNaN(certificationId)) {
      return NextResponse.json(
        { error: "Invalid certification ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // First check if certification exists
    const { data: existingCertification, error: fetchError } = await supabase
      .from("certifications")
      .select("id")
      .eq("id", certificationId)
      .single();

    if (fetchError || !existingCertification) {
      return NextResponse.json(
        { error: "Certification not found" },
        { status: 404 }
      );
    }

    // Delete the certification
    const { error } = await supabase
      .from("certifications")
      .delete()
      .eq("id", certificationId);

    if (error) {
      console.error("Failed to delete certification:", error);
      return NextResponse.json(
        { error: "Failed to delete certification", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting certification:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

