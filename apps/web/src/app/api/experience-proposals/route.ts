/**
 * Experience Proposals API - List and Create
 *
 * GET  /api/experience-proposals?session_id=1 - List all proposals for a session
 * GET  /api/experience-proposals?session_id=1&experience_id=1 - List proposals for specific experience
 * POST /api/experience-proposals - Create a new proposal
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { experienceProposalCreateSchema } from "./_lib/schema/experience-proposal.schema";

/**
 * GET /api/experience-proposals
 * List all proposals for a session, optionally filtered by experience_id.
 * Requires session_id query parameter.
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const sessionIdParam = searchParams.get("session_id");
    const experienceIdParam = searchParams.get("experience_id");

    if (!sessionIdParam) {
      return NextResponse.json(
        { error: "session_id query parameter is required" },
        { status: 400 }
      );
    }

    const sessionId = parseInt(sessionIdParam, 10);
    if (isNaN(sessionId)) {
      return NextResponse.json(
        { error: "Invalid session_id parameter" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Build query
    let query = supabase
      .from("experience_proposals")
      .select("*")
      .eq("session_id", sessionId)
      .order("created_at", { ascending: true });

    // Optionally filter by experience_id
    if (experienceIdParam) {
      const experienceId = parseInt(experienceIdParam, 10);
      if (isNaN(experienceId)) {
        return NextResponse.json(
          { error: "Invalid experience_id parameter" },
          { status: 400 }
        );
      }
      query = query.eq("experience_id", experienceId);
    }

    const { data: proposals, error } = await query;

    if (error) {
      console.error("Failed to list experience proposals:", error);
      return NextResponse.json(
        { error: "Failed to list experience proposals", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(proposals);
  } catch (error) {
    console.error("Unexpected error listing experience proposals:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/experience-proposals
 * Create a new experience proposal.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = experienceProposalCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Verify the session exists
    const { data: session, error: sessionError } = await supabase
      .from("job_intake_sessions")
      .select("id")
      .eq("id", parseResult.data.session_id)
      .single();

    if (sessionError || !session) {
      return NextResponse.json(
        { error: "Intake session not found" },
        { status: 404 }
      );
    }

    // Verify the experience exists
    const { data: experience, error: experienceError } = await supabase
      .from("experiences")
      .select("id")
      .eq("id", parseResult.data.experience_id)
      .single();

    if (experienceError || !experience) {
      return NextResponse.json(
        { error: "Experience not found" },
        { status: 404 }
      );
    }

    // If achievement_id is provided, verify it exists
    if (parseResult.data.achievement_id) {
      const { data: achievement, error: achievementError } = await supabase
        .from("achievements")
        .select("id")
        .eq("id", parseResult.data.achievement_id)
        .single();

      if (achievementError || !achievement) {
        return NextResponse.json(
          { error: "Achievement not found" },
          { status: 404 }
        );
      }
    }

    // Create the proposal
    const { data: proposal, error } = await supabase
      .from("experience_proposals")
      .insert({
        session_id: parseResult.data.session_id,
        proposal_type: parseResult.data.proposal_type,
        experience_id: parseResult.data.experience_id,
        achievement_id: parseResult.data.achievement_id ?? null,
        proposed_content: parseResult.data.proposed_content,
        original_proposed_content: parseResult.data.original_proposed_content,
        status: parseResult.data.status,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create experience proposal:", error);
      return NextResponse.json(
        { error: "Failed to create experience proposal", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(proposal, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating experience proposal:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

