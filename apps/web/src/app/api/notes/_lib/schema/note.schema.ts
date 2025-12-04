/**
 * Zod validation schemas for Note API routes.
 */

import { z } from "zod";

/**
 * Schema for creating a new note.
 */
export const noteCreateSchema = z.object({
  job_id: z.number().int().positive("Job ID must be a positive integer"),
  content: z.string().min(1, "Note content is required"),
});

export type NoteCreateInput = z.infer<typeof noteCreateSchema>;

/**
 * Schema for updating a note.
 */
export const noteUpdateSchema = z.object({
  content: z.string().min(1).optional(),
});

export type NoteUpdateInput = z.infer<typeof noteUpdateSchema>;

