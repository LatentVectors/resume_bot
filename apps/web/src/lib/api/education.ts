/**
 * Education API client endpoints.
 */

import { apiRequest } from "./client";
import type { Education, EducationInsert, EducationUpdate } from "@resume/database/types";

export const educationAPI = {
  /**
   * List all education entries for a user.
   */
  list: (userId: number): Promise<Education[]> => {
    const queryParams = new URLSearchParams({
      user_id: userId.toString(),
    });
    return apiRequest<Education[]>(`/api/education?${queryParams.toString()}`);
  },

  /**
   * Get a specific education entry.
   */
  get: (educationId: number): Promise<Education> => {
    return apiRequest<Education>(`/api/education/${educationId}`);
  },

  /**
   * Create a new education entry.
   */
  create: (params: { user_id: number; data: Omit<EducationInsert, "user_id"> }): Promise<Education> => {
    const queryParams = new URLSearchParams({
      user_id: params.user_id.toString(),
    });
    return apiRequest<Education>(`/api/education?${queryParams.toString()}`, {
      method: "POST",
      body: JSON.stringify(params.data),
    });
  },

  /**
   * Update an education entry.
   */
  update: (educationId: number, data: EducationUpdate): Promise<Education> => {
    return apiRequest<Education>(`/api/education/${educationId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete an education entry.
   */
  delete: (educationId: number): Promise<void> => {
    return apiRequest<void>(`/api/education/${educationId}`, {
      method: "DELETE",
    });
  },
};
