/**
 * Certifications API - List and Create
 *
 * GET  /api/certifications?user_id=1 - List all certifications for a user
 * POST /api/certifications?user_id=1 - Create a new certification
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { certificationCreateSchema } from "./_lib/schema/certification.schema";

/**
 * GET /api/certifications
 * List all certifications for a user.
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

    const { data: certifications, error } = await supabase
      .from("certifications")
      .select("*")
      .eq("user_id", userId)
      .order("date", { ascending: false });

    if (error) {
      console.error("Failed to list certifications:", error);
      return NextResponse.json(
        { error: "Failed to list certifications", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(certifications);
  } catch (error) {
    console.error("Unexpected error listing certifications:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/certifications
 * Create a new certification.
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
    const parseResult = certificationCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: certification, error } = await supabase
      .from("certifications")
      .insert({
        user_id: userId,
        ...parseResult.data,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create certification:", error);
      return NextResponse.json(
        { error: "Failed to create certification", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(certification, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating certification:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

