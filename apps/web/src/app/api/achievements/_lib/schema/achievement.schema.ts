/**
 * Zod validation schemas for Achievement API endpoints.
 */

import { z } from "zod";

/**
 * Schema for creating a new achievement.
 */
export const achievementCreateSchema = z.object({
  title: z.string().min(1, "Title is required"),
  content: z.string().min(1, "Content is required"),
  order: z.number().int().nonnegative().default(0),
});

export type AchievementCreateInput = z.infer<typeof achievementCreateSchema>;

/**
 * Schema for updating an achievement.
 * All fields are optional for partial updates.
 */
export const achievementUpdateSchema = z.object({
  title: z.string().min(1).optional(),
  content: z.string().min(1).optional(),
  order: z.number().int().nonnegative().optional(),
});

export type AchievementUpdateInput = z.infer<typeof achievementUpdateSchema>;

