/**
 * Zod validation schemas for Certification API endpoints.
 */

import { z } from "zod";

/**
 * Schema for creating a new certification.
 */
export const certificationCreateSchema = z.object({
  title: z.string().min(1, "Title is required"),
  institution: z.string().nullable().optional(),
  date: z.string().refine(
    (val) => !isNaN(Date.parse(val)),
    "Invalid date format. Use YYYY-MM-DD"
  ),
});

export type CertificationCreateInput = z.infer<typeof certificationCreateSchema>;

/**
 * Schema for updating a certification.
 * All fields are optional for partial updates.
 */
export const certificationUpdateSchema = z.object({
  title: z.string().min(1).optional(),
  institution: z.string().nullable().optional(),
  date: z
    .string()
    .refine((val) => !isNaN(Date.parse(val)), "Invalid date format. Use YYYY-MM-DD")
    .optional(),
});

export type CertificationUpdateInput = z.infer<typeof certificationUpdateSchema>;

