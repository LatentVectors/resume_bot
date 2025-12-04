/**
 * Zod validation schemas for Template API routes.
 */

import { z } from "zod";

/**
 * Valid template type values matching the PostgreSQL enum.
 */
export const templateTypeEnum = z.enum(["resume", "cover_letter"]);
export const templateTypeValues = templateTypeEnum.options;

export type TemplateTypeValue = z.infer<typeof templateTypeEnum>;

/**
 * Schema for creating a new template.
 */
export const templateCreateSchema = z.object({
  name: z.string().min(1, "Template name is required"),
  type: templateTypeEnum,
  html_content: z.string().min(1, "HTML content is required"),
  description: z.string().optional().nullable(),
  preview_image_url: z.string().url().optional().nullable(),
  is_default: z.boolean().optional().default(false),
  metadata: z.record(z.unknown()).optional().default({}),
});

export type TemplateCreateInput = z.infer<typeof templateCreateSchema>;

/**
 * Schema for updating a template.
 */
export const templateUpdateSchema = z.object({
  name: z.string().min(1).optional(),
  type: templateTypeEnum.optional(),
  html_content: z.string().min(1).optional(),
  description: z.string().optional().nullable(),
  preview_image_url: z.string().url().optional().nullable(),
  is_default: z.boolean().optional(),
  metadata: z.record(z.unknown()).optional(),
});

export type TemplateUpdateInput = z.infer<typeof templateUpdateSchema>;

