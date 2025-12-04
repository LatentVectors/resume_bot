/**
 * Zod validation schemas for Resume API routes.
 *
 * These schemas handle validation for resume version operations.
 * Note: The resumes table has been consolidated into resume_versions.
 * The "current" resume is the version with is_pinned=true.
 */

import { z } from "zod";

/**
 * Valid resume version event types matching the PostgreSQL enum.
 */
export const resumeVersionEventEnum = z.enum(["generate", "save", "reset"]);

export type ResumeVersionEventValue = z.infer<typeof resumeVersionEventEnum>;

/**
 * Schema for creating a resume version.
 * In the consolidated model, this is the primary way to create/update resumes.
 */
export const resumeVersionCreateSchema = z.object({
  job_id: z.number().int().positive("job_id is required"),
  resume_json: z.string().min(1, "resume_json is required"),
  template_name: z.string().min(1, "template_name is required"),
  event_type: resumeVersionEventEnum,
  parent_version_id: z.number().int().positive().optional().nullable(),
  created_by_user_id: z
    .number()
    .int()
    .positive("created_by_user_id is required"),
  is_pinned: z.boolean().optional().default(false),
});

export type ResumeVersionCreateInput = z.infer<
  typeof resumeVersionCreateSchema
>;

/**
 * Schema for updating a resume version.
 */
export const resumeVersionUpdateSchema = z.object({
  resume_json: z.string().min(1).optional(),
  template_name: z.string().min(1).optional(),
  is_pinned: z.boolean().optional(),
  locked: z.boolean().optional(),
});

export type ResumeVersionUpdateInput = z.infer<
  typeof resumeVersionUpdateSchema
>;

/**
 * Schema for pinning a resume version.
 */
export const resumePinSchema = z.object({
  version_id: z.number().int().positive("version_id is required"),
});

export type ResumePinInput = z.infer<typeof resumePinSchema>;
