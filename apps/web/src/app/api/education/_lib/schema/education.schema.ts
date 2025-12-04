/**
 * Zod validation schemas for Education API endpoints.
 */

import { z } from "zod";

/**
 * Schema for creating a new education entry.
 */
export const educationCreateSchema = z.object({
  institution: z.string().min(1, "Institution name is required"),
  degree: z.string().min(1, "Degree is required"),
  major: z.string().min(1, "Major is required"),
  grad_date: z.string().refine(
    (val) => !isNaN(Date.parse(val)),
    "Invalid date format. Use YYYY-MM-DD"
  ),
});

export type EducationCreateInput = z.infer<typeof educationCreateSchema>;

/**
 * Schema for updating an education entry.
 * All fields are optional for partial updates.
 */
export const educationUpdateSchema = z.object({
  institution: z.string().min(1).optional(),
  degree: z.string().min(1).optional(),
  major: z.string().min(1).optional(),
  grad_date: z
    .string()
    .refine((val) => !isNaN(Date.parse(val)), "Invalid date format. Use YYYY-MM-DD")
    .optional(),
});

export type EducationUpdateInput = z.infer<typeof educationUpdateSchema>;

