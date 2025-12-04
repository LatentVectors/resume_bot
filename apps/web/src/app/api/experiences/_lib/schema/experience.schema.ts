/**
 * Zod validation schemas for Experience API endpoints.
 */

import { z } from "zod";

/**
 * Schema for skills array.
 * Skills are stored as a JSONB array of strings.
 */
const skillsSchema = z.array(z.string()).default([]);

/**
 * Schema for creating a new experience.
 */
export const experienceCreateSchema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  job_title: z.string().min(1, "Job title is required"),
  start_date: z.string().refine(
    (val) => !isNaN(Date.parse(val)),
    "Invalid date format. Use YYYY-MM-DD"
  ),
  end_date: z
    .string()
    .refine((val) => !isNaN(Date.parse(val)), "Invalid date format. Use YYYY-MM-DD")
    .nullable()
    .optional(),
  location: z.string().nullable().optional(),
  company_overview: z.string().nullable().optional(),
  role_overview: z.string().nullable().optional(),
  skills: skillsSchema.optional(),
});

export type ExperienceCreateInput = z.infer<typeof experienceCreateSchema>;

/**
 * Schema for updating an experience.
 * All fields are optional for partial updates.
 */
export const experienceUpdateSchema = z.object({
  company_name: z.string().min(1).optional(),
  job_title: z.string().min(1).optional(),
  start_date: z
    .string()
    .refine((val) => !isNaN(Date.parse(val)), "Invalid date format. Use YYYY-MM-DD")
    .optional(),
  end_date: z
    .string()
    .refine((val) => !isNaN(Date.parse(val)), "Invalid date format. Use YYYY-MM-DD")
    .nullable()
    .optional(),
  location: z.string().nullable().optional(),
  company_overview: z.string().nullable().optional(),
  role_overview: z.string().nullable().optional(),
  skills: skillsSchema.optional(),
});

export type ExperienceUpdateInput = z.infer<typeof experienceUpdateSchema>;

