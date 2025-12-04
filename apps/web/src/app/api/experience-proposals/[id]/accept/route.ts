/**
 * Experience Proposals API - Accept Proposal
 *
 * PATCH /api/experience-proposals/[id]/accept - Accept a proposal and apply changes
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import type { ExperienceProposal } from "@resume/database/types";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * Apply the proposal changes to the experience/achievement.
 * This implements the business logic for accepting proposals.
 */
async function applyProposalChanges(
  supabase: Awaited<ReturnType<typeof getSupabaseServerClient>>,
  proposal: ExperienceProposal
): Promise<boolean> {
  const { proposal_type, experience_id, achievement_id, proposed_content } =
    proposal;
  const content = proposed_content as Record<string, unknown>;

  try {
    switch (proposal_type) {
      case "achievement_add": {
        // Add a new achievement
        const { error } = await supabase.from("achievements").insert({
          experience_id: experience_id,
          title: (content.title as string) || "",
          content: (content.content as string) || "",
          order: (content.order as number) || 0,
        });
        return !error;
      }

      case "achievement_update": {
        // Update an existing achievement
        if (!achievement_id) return false;
        const { error } = await supabase
          .from("achievements")
          .update({
            title: content.title as string,
            content: content.content as string,
          })
          .eq("id", achievement_id);
        return !error;
      }

      case "achievement_delete": {
        // Delete an achievement
        if (!achievement_id) return false;
        const { error } = await supabase
          .from("achievements")
          .delete()
          .eq("id", achievement_id);
        return !error;
      }

      case "skill_add": {
        // Add a skill to the experience
        const { data: experience, error: fetchError } = await supabase
          .from("experiences")
          .select("skills")
          .eq("id", experience_id)
          .single();

        if (fetchError || !experience) return false;

        const currentSkills = (experience.skills as string[]) || [];
        const newSkill = content.skill as string;
        if (!newSkill || currentSkills.includes(newSkill)) return true;

        const { error } = await supabase
          .from("experiences")
          .update({ skills: [...currentSkills, newSkill] })
          .eq("id", experience_id);
        return !error;
      }

      case "skill_delete": {
        // Remove a skill from the experience
        const { data: experience, error: fetchError } = await supabase
          .from("experiences")
          .select("skills")
          .eq("id", experience_id)
          .single();

        if (fetchError || !experience) return false;

        const currentSkills = (experience.skills as string[]) || [];
        const skillToRemove = content.skill as string;
        const updatedSkills = currentSkills.filter((s) => s !== skillToRemove);

        const { error } = await supabase
          .from("experiences")
          .update({ skills: updatedSkills })
          .eq("id", experience_id);
        return !error;
      }

      case "role_overview_update": {
        // Update the role overview
        const { error } = await supabase
          .from("experiences")
          .update({ role_overview: content.role_overview as string })
          .eq("id", experience_id);
        return !error;
      }

      case "company_overview_update": {
        // Update the company overview
        const { error } = await supabase
          .from("experiences")
          .update({ company_overview: content.company_overview as string })
          .eq("id", experience_id);
        return !error;
      }

      default:
        console.warn(`Unknown proposal type: ${proposal_type}`);
        return false;
    }
  } catch (error) {
    console.error("Error applying proposal changes:", error);
    return false;
  }
}

/**
 * PATCH /api/experience-proposals/[id]/accept
 * Accept a proposal and apply the changes.
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

    // Apply the proposal changes
    const success = await applyProposalChanges(supabase, proposal);
    if (!success) {
      return NextResponse.json(
        { error: "Failed to apply proposal changes" },
        { status: 500 }
      );
    }

    // Update proposal status to accepted
    const { data: updatedProposal, error: updateError } = await supabase
      .from("experience_proposals")
      .update({ status: "accepted" })
      .eq("id", proposalId)
      .select()
      .single();

    if (updateError) {
      console.error("Failed to update proposal status:", updateError);
      return NextResponse.json(
        { error: "Failed to update proposal status", details: updateError.message },
        { status: 500 }
      );
    }

    return NextResponse.json(updatedProposal);
  } catch (error) {
    console.error("Unexpected error accepting proposal:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

