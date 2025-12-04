/**
 * Zod validation schemas for Job API routes.
 *
 * These schemas handle validation for job creation, updates, and non-standard operations
 * like bulk delete, favorite toggle, status update, and apply actions.
 */

import { z } from "zod";

/**
 * Valid job status values matching the PostgreSQL enum.
 */
export const jobStatusValues = [
  "Saved",
  "Applied",
  "Interviewing",
  "Not Selected",
  "No Offer",
  "Hired",
] as const;

export const jobStatusEnum = z.enum(jobStatusValues);

export type JobStatusValue = z.infer<typeof jobStatusEnum>;

/**
 * Schema for creating a new job.
 */
export const jobCreateSchema = z.object({
  job_description: z.string().min(1, "Job description is required"),
  company_name: z.string().optional().nullable(),
  job_title: z.string().optional().nullable(),
  is_favorite: z.boolean().optional().default(false),
  status: jobStatusEnum.optional().default("Saved"),
});

export type JobCreateInput = z.infer<typeof jobCreateSchema>;

/**
 * Schema for updating a job.
 */
export const jobUpdateSchema = z.object({
  job_description: z.string().min(1).optional(),
  company_name: z.string().optional().nullable(),
  job_title: z.string().optional().nullable(),
  is_favorite: z.boolean().optional(),
  status: jobStatusEnum.optional(),
  resume_chat_thread_id: z.string().optional().nullable(),
});

export type JobUpdateInput = z.infer<typeof jobUpdateSchema>;

/**
 * Schema for bulk delete request.
 */
export const bulkDeleteSchema = z.object({
  job_ids: z
    .array(z.number().int().positive())
    .min(1, "At least one job ID is required"),
});

export type BulkDeleteInput = z.infer<typeof bulkDeleteSchema>;

/**
 * Schema for favorite toggle (via query param or body).
 */
export const favoriteToggleSchema = z.object({
  favorite: z.boolean(),
});

export type FavoriteToggleInput = z.infer<typeof favoriteToggleSchema>;

/**
 * Schema for status update.
 */
export const statusUpdateSchema = z.object({
  status: jobStatusEnum,
});

export type StatusUpdateInput = z.infer<typeof statusUpdateSchema>;
