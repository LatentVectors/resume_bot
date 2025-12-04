/**
 * Experience Proposals API - Reject Proposal
 *
 * PATCH /api/experience-proposals/[id]/reject - Reject a proposal
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * PATCH /api/experience-proposals/[id]/reject
 * Reject a proposal (mark as rejected without applying changes).
 */
export async function PATCH(_req: NextRequest, { params }: RouteParams) {
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

    // Get the proposal
    const { data: proposal, error: fetchError } = await supabase
      .from("experience_proposals")
      .select("*")
      .eq("id", proposalId)
      .single();

    if (fetchError || !proposal) {
      return NextResponse.json(
        { error: "Experience proposal not found" },
        { status: 404 }
      );
    }

    // Check if already processed
    if (proposal.status !== "pending") {
      return NextResponse.json(
        { error: `Proposal is already ${proposal.status}` },
        { status: 400 }
      );
    }

    // Update proposal status to rejected
    const { data: updatedProposal, error: updateError } = await supabase
      .from("experience_proposals")
      .update({ status: "rejected" })
      .eq("id", proposalId)
      .select()
      .single();

    if (updateError) {
      console.error("Failed to reject proposal:", updateError);
      return NextResponse.json(
        { error: "Failed to reject proposal", details: updateError.message },
        { status: 500 }
      );
    }

    return NextResponse.json(updatedProposal);
  } catch (error) {
    console.error("Unexpected error rejecting proposal:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

