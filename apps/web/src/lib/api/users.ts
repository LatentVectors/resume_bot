/**
 * Users API client endpoints.
 */

import { apiRequest } from "./client";
import type { User, UserInsert, UserUpdate } from "@resume/database/types";

export const usersAPI = {
  /**
   * List all users.
   */
  list: (): Promise<User[]> => {
    return apiRequest<User[]>("/api/users");
  },

  /**
   * Get current user (for single-user mode).
   */
  getCurrent: (): Promise<User> => {
    return apiRequest<User>("/api/users/current");
  },

  /**
   * Get a specific user.
   */
  get: (userId: number): Promise<User> => {
    return apiRequest<User>(`/api/users/${userId}`);
  },

  /**
   * Create a new user.
   */
  create: (data: UserInsert): Promise<User> => {
    return apiRequest<User>("/api/users", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Update a user.
   */
  update: (userId: number, data: UserUpdate): Promise<User> => {
    return apiRequest<User>(`/api/users/${userId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a user.
   * Note: This endpoint may not be fully implemented on the backend.
   */
  delete: (userId: number): Promise<void> => {
    return apiRequest<void>(`/api/users/${userId}`, {
      method: "DELETE",
    });
  },

  /**
   * Get statistics for a user's job applications.
   */
  getStats: (userId: number): Promise<{
    jobs_applied_7_days: number;
    jobs_applied_30_days: number;
    total_jobs_saved: number;
    total_jobs_applied: number;
    total_interviews: number;
    total_offers: number;
    total_favorites: number;
    success_rate: number | null;
  }> => {
    return apiRequest(`/api/users/${userId}/stats`);
  },
};
