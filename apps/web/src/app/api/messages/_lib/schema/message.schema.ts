/**
 * Zod validation schemas for Message API routes.
 */

import { z } from "zod";

/**
 * Valid message channel values matching the PostgreSQL enum.
 */
export const messageChannelEnum = z.enum(["email", "linkedin"]);
export const messageChannelValues = messageChannelEnum.options;

export type MessageChannelValue = z.infer<typeof messageChannelEnum>;

/**
 * Schema for creating a new message.
 */
export const messageCreateSchema = z.object({
  job_id: z.number().int().positive("Job ID must be a positive integer"),
  channel: messageChannelEnum,
  body: z.string().min(1, "Message body is required"),
  sent_at: z.string().datetime().optional().nullable(),
});

export type MessageCreateInput = z.infer<typeof messageCreateSchema>;

/**
 * Schema for updating a message.
 */
export const messageUpdateSchema = z.object({
  channel: messageChannelEnum.optional(),
  body: z.string().min(1).optional(),
  sent_at: z.string().datetime().optional().nullable(),
});

export type MessageUpdateInput = z.infer<typeof messageUpdateSchema>;

