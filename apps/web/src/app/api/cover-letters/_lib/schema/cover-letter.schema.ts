/**
 * Zod validation schemas for Cover Letter API routes.
 *
 * These schemas handle validation for cover letter version operations.
 * Note: The cover_letters table has been consolidated into cover_letter_versions.
 * The "current" cover letter is the version with is_pinned=true.
 */

import { z } from "zod";

/**
 * Valid cover letter version event types matching the PostgreSQL enum.
 */
export const coverLetterVersionEventEnum = z.enum(["generate", "save", "reset"]);

export type CoverLetterVersionEventValue = z.infer<typeof coverLetterVersionEventEnum>;

/**
 * Schema for creating a cover letter version.
 * In the consolidated model, this is the primary way to create/update cover letters.
 */
export const coverLetterVersionCreateSchema = z.object({
  job_id: z.number().int().positive("job_id is required"),
  cover_letter_json: z.string().min(1, "cover_letter_json is required"),
  template_name: z.string().min(1).optional().default("cover_000.html"),
  event_type: coverLetterVersionEventEnum,
  parent_version_id: z.number().int().positive().optional().nullable(),
  created_by_user_id: z.number().int().positive("created_by_user_id is required"),
  is_pinned: z.boolean().optional().default(false),
});

export type CoverLetterVersionCreateInput = z.infer<typeof coverLetterVersionCreateSchema>;

/**
 * Schema for updating a cover letter version.
 */
export const coverLetterVersionUpdateSchema = z.object({
  cover_letter_json: z.string().min(1).optional(),
  template_name: z.string().min(1).optional(),
  is_pinned: z.boolean().optional(),
  locked: z.boolean().optional(),
});

export type CoverLetterVersionUpdateInput = z.infer<typeof coverLetterVersionUpdateSchema>;

/**
 * Schema for pinning a cover letter version.
 */
export const coverLetterPinSchema = z.object({
  version_id: z.number().int().positive("version_id is required"),
});

export type CoverLetterPinInput = z.infer<typeof coverLetterPinSchema>;
