/**
 * Zod validation schemas for Job Intake Session API endpoints.
 */

import { z } from "zod";

/**
 * Schema for updating an intake session.
 * Supports updating current step, marking steps as completed, and saving analysis data.
 */
export const intakeSessionUpdateSchema = z.object({
  current_step: z
    .number()
    .int()
    .min(1)
    .max(3)
    .optional()
    .describe("Current step (1-3)"),
  step_completed: z
    .number()
    .int()
    .min(1)
    .max(3)
    .optional()
    .describe("Step to mark as completed (1-3)"),
  step1_completed: z.boolean().optional(),
  step2_completed: z.boolean().optional(),
  step3_completed: z.boolean().optional(),
  gap_analysis: z.string().nullable().optional().describe("Gap analysis text"),
  stakeholder_analysis: z
    .string()
    .nullable()
    .optional()
    .describe("Stakeholder analysis text"),
  resume_chat_thread_id: z
    .string()
    .nullable()
    .optional()
    .describe("Resume chat thread ID"),
  completed_at: z
    .string()
    .refine((val) => !isNaN(Date.parse(val)), "Invalid date format")
    .nullable()
    .optional()
    .describe("Completion timestamp"),
});

export type IntakeSessionUpdateInput = z.infer<typeof intakeSessionUpdateSchema>;

/**
 * Schema for saving chat messages.
 */
export const chatMessagesSchema = z.object({
  messages: z.array(z.record(z.unknown())).describe("Array of message objects"),
});

export type ChatMessagesInput = z.infer<typeof chatMessagesSchema>;

