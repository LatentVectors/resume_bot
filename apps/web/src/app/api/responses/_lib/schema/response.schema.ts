/**
 * Zod validation schemas for Response API routes.
 */

import { z } from "zod";

/**
 * Valid response source values matching the PostgreSQL enum.
 */
export const responseSourceEnum = z.enum(["manual", "application"]);
export const responseSourceValues = responseSourceEnum.options;

export type ResponseSourceValue = z.infer<typeof responseSourceEnum>;

/**
 * Schema for creating a new response.
 */
export const responseCreateSchema = z.object({
  job_id: z.number().int().positive().optional().nullable(),
  source: responseSourceEnum,
  prompt: z.string().min(1, "Prompt is required"),
  response: z.string().min(1, "Response is required"),
  ignore: z.boolean().optional().default(false),
  locked: z.boolean().optional().default(false),
});

export type ResponseCreateInput = z.infer<typeof responseCreateSchema>;

/**
 * Schema for updating a response.
 */
export const responseUpdateSchema = z.object({
  job_id: z.number().int().positive().optional().nullable(),
  source: responseSourceEnum.optional(),
  prompt: z.string().min(1).optional(),
  response: z.string().min(1).optional(),
  ignore: z.boolean().optional(),
  locked: z.boolean().optional(),
});

export type ResponseUpdateInput = z.infer<typeof responseUpdateSchema>;

