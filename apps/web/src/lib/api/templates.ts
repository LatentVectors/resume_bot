/**
 * Templates API client endpoints.
 */

import { apiRequest } from "./client";
import type { Template } from "@resume/database/types";

export const templatesAPI = {
  /**
   * List all available resume templates.
   */
  listResumeTemplates: (): Promise<Template[]> => {
    return apiRequest<Template[]>("/api/templates?type=resume");
  },

  /**
   * List all available cover letter templates.
   */
  listCoverLetterTemplates: (): Promise<Template[]> => {
    return apiRequest<Template[]>("/api/templates?type=cover_letter");
  },

  /**
   * List all templates.
   */
  list: (): Promise<Template[]> => {
    return apiRequest<Template[]>("/api/templates");
  },

  /**
   * Get a specific template by ID.
   */
  get: (templateId: number): Promise<Template> => {
    return apiRequest<Template>(`/api/templates/${templateId}`);
  },
};
