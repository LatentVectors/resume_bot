/**
 * Current User API
 *
 * GET /api/users/current - Get the current user
 *
 * In single-user mode, this returns the first (and only) user in the database.
 */

import { NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";

/**
 * GET /api/users/current
 * Get the current user (single-user mode).
 */
export async function GET() {
  try {
    const supabase = await getSupabaseServerClient();

    // In single-user mode, just get the first user
    const { data: user, error } = await supabase
      .from("users")
      .select("*")
      .order("id", { ascending: true })
      .limit(1)
      .single();

    if (error) {
      console.error("Failed to get current user:", error);
      return NextResponse.json(
        { error: "Failed to get current user", details: error.message },
        { status: 500 }
      );
    }

    if (!user) {
      return NextResponse.json(
        { error: "No user found in database" },
        { status: 404 }
      );
    }

    return NextResponse.json(user);
  } catch (error) {
    console.error("Unexpected error getting current user:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

