/**
 * Zod validation schemas for User API endpoints.
 */

import { z } from "zod";

/**
 * Schema for creating a new user.
 */
export const userCreateSchema = z.object({
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  phone_number: z.string().nullable().optional(),
  email: z.string().email().nullable().optional(),
  address: z.string().nullable().optional(),
  city: z.string().nullable().optional(),
  state: z.string().nullable().optional(),
  zip_code: z.string().nullable().optional(),
  linkedin_url: z.string().url().nullable().optional(),
  github_url: z.string().url().nullable().optional(),
  website_url: z.string().url().nullable().optional(),
});

export type UserCreateInput = z.infer<typeof userCreateSchema>;

/**
 * Schema for updating a user.
 * All fields are optional for partial updates.
 */
export const userUpdateSchema = z.object({
  first_name: z.string().min(1).optional(),
  last_name: z.string().min(1).optional(),
  phone_number: z.string().nullable().optional(),
  email: z.string().email().nullable().optional(),
  address: z.string().nullable().optional(),
  city: z.string().nullable().optional(),
  state: z.string().nullable().optional(),
  zip_code: z.string().nullable().optional(),
  linkedin_url: z.string().url().nullable().optional(),
  github_url: z.string().url().nullable().optional(),
  website_url: z.string().url().nullable().optional(),
});

export type UserUpdateInput = z.infer<typeof userUpdateSchema>;

