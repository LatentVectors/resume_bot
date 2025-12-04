/**
 * Users API - List and Create
 *
 * GET  /api/users - List all users
 * POST /api/users - Create a new user
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { userCreateSchema } from "./_lib/schema/user.schema";

/**
 * GET /api/users
 * List all users.
 */
export async function GET() {
  try {
    const supabase = await getSupabaseServerClient();

    const { data: users, error } = await supabase
      .from("users")
      .select("*")
      .order("id", { ascending: true });

    if (error) {
      console.error("Failed to list users:", error);
      return NextResponse.json(
        { error: "Failed to list users", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(users);
  } catch (error) {
    console.error("Unexpected error listing users:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/users
 * Create a new user.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = userCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: user, error } = await supabase
      .from("users")
      .insert(parseResult.data)
      .select()
      .single();

    if (error) {
      console.error("Failed to create user:", error);
      return NextResponse.json(
        { error: "Failed to create user", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(user, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating user:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

