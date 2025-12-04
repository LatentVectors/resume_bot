/**
 * Zod validation schemas for Experience Proposal API endpoints.
 */

import { z } from "zod";

/**
 * Valid proposal type values.
 */
export const proposalTypeValues = [
  "achievement_add",
  "achievement_update",
  "achievement_delete",
  "skill_add",
  "skill_delete",
  "role_overview_update",
  "company_overview_update",
] as const;

export const proposalTypeSchema = z.enum(proposalTypeValues);

export type ProposalTypeInput = z.infer<typeof proposalTypeSchema>;

/**
 * Valid proposal status values.
 */
export const proposalStatusValues = ["pending", "accepted", "rejected"] as const;

export const proposalStatusSchema = z.enum(proposalStatusValues);

export type ProposalStatusInput = z.infer<typeof proposalStatusSchema>;

/**
 * Schema for creating a new experience proposal.
 */
export const experienceProposalCreateSchema = z.object({
  session_id: z.number().int().positive().describe("Job intake session ID"),
  proposal_type: proposalTypeSchema.describe("Type of proposal"),
  experience_id: z.number().int().positive().describe("Experience ID"),
  achievement_id: z
    .number()
    .int()
    .positive()
    .nullable()
    .optional()
    .describe("Achievement ID (for achievement proposals)"),
  proposed_content: z
    .record(z.unknown())
    .describe("JSON object containing proposal data"),
  original_proposed_content: z
    .record(z.unknown())
    .describe("JSON object of original proposal"),
  status: proposalStatusSchema.optional().default("pending").describe("Proposal status"),
});

export type ExperienceProposalCreateInput = z.infer<
  typeof experienceProposalCreateSchema
>;

/**
 * Schema for updating an experience proposal.
 * All fields are optional for partial updates.
 */
export const experienceProposalUpdateSchema = z.object({
  proposed_content: z
    .record(z.unknown())
    .optional()
    .describe("JSON object containing proposal data"),
  status: proposalStatusSchema.optional().describe("Proposal status"),
});

export type ExperienceProposalUpdateInput = z.infer<
  typeof experienceProposalUpdateSchema
>;

