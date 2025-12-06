/**
 * Jobs API client endpoints.
 */

import { apiRequest } from "./client";
import type { Job, JobInsert, JobUpdate, JobStatus, JobIntakeSession } from "@resume/database/types";

/**
 * Response type for the jobs list endpoint.
 */
interface JobsListResponse {
  items: Job[];
  total: number;
  skip: number;
  limit: number;
}

export const jobsAPI = {
  /**
   * List all jobs for a user with pagination.
   */
  list: async (params: {
    user_id: number;
    status_filter?: JobStatus | null;
    favorite_only?: boolean;
    skip?: number;
    limit?: number;
  }): Promise<JobsListResponse> => {
    const queryParams = new URLSearchParams({
      user_id: params.user_id.toString(),
    });
    if (params.status_filter) {
      queryParams.append("status_filter", params.status_filter);
    }
    if (params.favorite_only) {
      queryParams.append("favorite_only", "true");
    }
    if (params.skip !== undefined) {
      queryParams.append("skip", params.skip.toString());
    }
    if (params.limit !== undefined) {
      queryParams.append("limit", params.limit.toString());
    }
    return apiRequest<JobsListResponse>(`/api/jobs?${queryParams.toString()}`);
  },

  /**
   * Bulk delete jobs.
   */
  bulkDelete: (jobIds: number[]): Promise<{ successful: number; failed: number }> => {
    return apiRequest(`/api/jobs/bulk-delete`, {
      method: "DELETE",
      body: JSON.stringify({ job_ids: jobIds }),
    });
  },

  /**
   * Get a specific job.
   */
  get: (jobId: number): Promise<Job> => {
    return apiRequest<Job>(`/api/jobs/${jobId}`);
  },

  /**
   * Create a new job.
   */
  create: (params: { user_id: number; data: Omit<JobInsert, "user_id"> }): Promise<Job> => {
    const queryParams = new URLSearchParams({
      user_id: params.user_id.toString(),
    });
    return apiRequest<Job>(`/api/jobs?${queryParams.toString()}`, {
      method: "POST",
      body: JSON.stringify(params.data),
    });
  },

  /**
   * Update a job.
   */
  update: (jobId: number, data: JobUpdate): Promise<Job> => {
    return apiRequest<Job>(`/api/jobs/${jobId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a job.
   */
  delete: (jobId: number): Promise<void> => {
    return apiRequest<void>(`/api/jobs/${jobId}`, {
      method: "DELETE",
    });
  },

  /**
   * Toggle favorite status for a job.
   */
  toggleFavorite: (jobId: number, favorite: boolean): Promise<Job> => {
    const queryParams = new URLSearchParams({
      favorite: favorite.toString(),
    });
    return apiRequest<Job>(`/api/jobs/${jobId}/favorite?${queryParams.toString()}`, {
      method: "PATCH",
    });
  },

  /**
   * Update job status.
   */
  updateStatus: (jobId: number, status: JobStatus): Promise<Job> => {
    const queryParams = new URLSearchParams({
      status: status,
    });
    return apiRequest<Job>(`/api/jobs/${jobId}/status?${queryParams.toString()}`, {
      method: "PATCH",
    });
  },

  /**
   * Mark a job as applied.
   */
  markAsApplied: (jobId: number): Promise<Job> => {
    return apiRequest<Job>(`/api/jobs/${jobId}/apply`, {
      method: "POST",
    });
  },

  /**
   * Get intake session for a job.
   */
  getIntakeSession: (jobId: number): Promise<JobIntakeSession> => {
    return apiRequest(`/api/jobs/${jobId}/intake-session`);
  },

  /**
   * Create intake session for a job.
   */
  createIntakeSession: (jobId: number): Promise<JobIntakeSession> => {
    return apiRequest(`/api/jobs/${jobId}/intake-session`, {
      method: "POST",
    });
  },

  /**
   * Update intake session for a job.
   */
  updateIntakeSession: (jobId: number, params: {
    current_step?: number;
    step_completed?: number;
    gap_analysis?: string;
    stakeholder_analysis?: string;
  }): Promise<JobIntakeSession> => {
    return apiRequest(`/api/jobs/${jobId}/intake-session`, {
      method: "PATCH",
      body: JSON.stringify(params),
    });
  },

  /**
   * Get chat messages for an intake session step.
   */
  getIntakeSessionMessages: (jobId: number, sessionId: number, step: number): Promise<Array<{
    role: string;
    content: string;
    tool_calls?: Array<{ [key: string]: unknown }> | null;
    tool_call_id?: string | null;
  }>> => {
    return apiRequest(`/api/jobs/${jobId}/intake-session/${sessionId}/messages?step=${step}`);
  },

  /**
   * Save chat messages for an intake session step.
   */
  saveIntakeSessionMessages: (jobId: number, sessionId: number, step: number, messages: Array<{
    role: string;
    content: string;
    tool_calls?: Array<{ [key: string]: unknown }> | null;
    tool_call_id?: string | null;
  }>): Promise<void> => {
    return apiRequest(`/api/jobs/${jobId}/intake-session/${sessionId}/messages?step=${step}`, {
      method: "POST",
      body: JSON.stringify({ messages }),
    });
  },
};
