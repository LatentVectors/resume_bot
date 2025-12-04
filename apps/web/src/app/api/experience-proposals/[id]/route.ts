/**
 * Experience Proposals API - Single Proposal Operations
 *
 * GET    /api/experience-proposals/[id] - Get a proposal by ID
 * PATCH  /api/experience-proposals/[id] - Update a proposal
 * DELETE /api/experience-proposals/[id] - Delete a proposal
 *
 * Special endpoint aliases:
 * PATCH  /api/experience-proposals/[id]/accept - Accept a proposal
 * PATCH  /api/experience-proposals/[id]/reject - Reject a proposal
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { experienceProposalUpdateSchema } from "../_lib/schema/experience-proposal.schema";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/experience-proposals/[id]
 * Get an experience proposal by ID.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const proposalId = parseInt(id, 10);

    if (isNaN(proposalId)) {
      return NextResponse.json(
        { error: "Invalid proposal ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: proposal, error } = await supabase
      .from("experience_proposals")
      .select("*")
      .eq("id", proposalId)
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Experience proposal not found" },
          { status: 404 }
        );
      }
      console.error("Failed to get experience proposal:", error);
      return NextResponse.json(
        { error: "Failed to get experience proposal", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(proposal);
  } catch (error) {
    console.error("Unexpected error getting experience proposal:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * PATCH /api/experience-proposals/[id]
 * Update an experience proposal.
 */
export async function PATCH(req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const proposalId = parseInt(id, 10);

    if (isNaN(proposalId)) {
      return NextResponse.json(
        { error: "Invalid proposal ID" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = experienceProposalUpdateSchema.safeParse(body);
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

    const { data: proposal, error } = await supabase
      .from("experience_proposals")
      .update(parseResult.data)
      .eq("id", proposalId)
      .select()
      .single();

    if (error) {
      if (error.code === "PGRST116") {
        return NextResponse.json(
          { error: "Experience proposal not found" },
          { status: 404 }
        );
      }
      console.error("Failed to update experience proposal:", error);
      return NextResponse.json(
        { error: "Failed to update experience proposal", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(proposal);
  } catch (error) {
    console.error("Unexpected error updating experience proposal:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * DELETE /api/experience-proposals/[id]
 * Delete an experience proposal.
 */
export async function DELETE(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const proposalId = parseInt(id, 10);

    if (isNaN(proposalId)) {
      return NextResponse.json(
        { error: "Invalid proposal ID" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // First check if proposal exists
    const { data: existingProposal, error: fetchError } = await supabase
      .from("experience_proposals")
      .select("id")
      .eq("id", proposalId)
      .single();

    if (fetchError || !existingProposal) {
      return NextResponse.json(
        { error: "Experience proposal not found" },
        { status: 404 }
      );
    }

    // Delete the proposal
    const { error } = await supabase
      .from("experience_proposals")
      .delete()
      .eq("id", proposalId);

    if (error) {
      console.error("Failed to delete experience proposal:", error);
      return NextResponse.json(
        { error: "Failed to delete experience proposal", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error deleting experience proposal:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

