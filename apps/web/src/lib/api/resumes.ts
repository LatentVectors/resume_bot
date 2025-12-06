/**
 * Resumes API client endpoints.
 *
 * Note: The resumes table has been consolidated into resume_versions.
 * The "current" resume for a job is the version with is_pinned=true.
 * All operations now work with resume_versions directly.
 */

import { apiRequest } from "./client";
import type { ResumeVersion } from "@resume/database/types";

/**
 * Resume data type for resume JSON content.
 */
export interface ResumeData {
  summary?: string;
  experiences?: Array<{
    id?: number;
    company?: string;
    title?: string;
    start_date?: string;
    end_date?: string | null;
    location?: string;
    achievements?: Array<{
      id?: number;
      text: string;
    }>;
  }>;
  education?: Array<{
    id?: number;
    institution?: string;
    degree?: string;
    field?: string;
    graduation_date?: string;
    gpa?: string | null;
  }>;
  certifications?: Array<{
    id?: number;
    name?: string;
    issuing_organization?: string;
    issue_date?: string;
    expiration_date?: string | null;
  }>;
  skills?: string[];
  [key: string]: unknown;
}

/**
 * Resume preview request type.
 */
export interface ResumePreviewRequest {
  resume_data: ResumeData;
  template_name: string;
}

/**
 * Input for creating a resume version.
 */
export interface ResumeVersionCreateInput {
  job_id: number;
  resume_json: string;
  template_name: string;
  event_type: "generate" | "save" | "reset";
  parent_version_id?: number | null;
  created_by_user_id: number;
  is_pinned?: boolean;
}

/**
 * Input for updating a resume version.
 */
export interface ResumeVersionUpdateInput {
  resume_json?: string;
  template_name?: string;
  is_pinned?: boolean;
  locked?: boolean;
}

export const resumesAPI = {
  /**
   * List pinned resume versions for a job (the "current" resumes).
   * In the consolidated model, there's at most one pinned version per job.
   */
  listByJob: (jobId: number): Promise<ResumeVersion[]> => {
    const queryParams = new URLSearchParams({
      job_id: jobId.toString(),
    });
    return apiRequest<ResumeVersion[]>(`/api/resumes?${queryParams.toString()}`);
  },

  /**
   * Get current (pinned) resume for a job.
   * Returns the pinned version for the job.
   * @throws Error if no pinned resume exists for the job
   */
  getCurrent: async (jobId: number): Promise<ResumeVersion> => {
    const resumes = await resumesAPI.listByJob(jobId);
    if (resumes.length === 0) {
      throw new Error("No resume found for this job");
    }
    return resumes[0];
  },

  /**
   * Get current (pinned) resume for a job, or null if none exists.
   */
  getCurrentOrNull: async (jobId: number): Promise<ResumeVersion | null> => {
    const resumes = await resumesAPI.listByJob(jobId);
    return resumes.length > 0 ? resumes[0] : null;
  },

  /**
   * Get a specific resume version by ID.
   */
  get: (versionId: number): Promise<ResumeVersion> => {
    return apiRequest<ResumeVersion>(`/api/resumes/${versionId}`);
  },

  /**
   * Create a new resume version.
   * If is_pinned is true, will unpin any existing pinned version for the job.
   */
  create: (data: ResumeVersionCreateInput): Promise<ResumeVersion> => {
    return apiRequest<ResumeVersion>(`/api/resumes`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Update a resume version.
   * If is_pinned is set to true, will unpin any existing pinned version for the job.
   */
  update: (versionId: number, data: ResumeVersionUpdateInput): Promise<ResumeVersion> => {
    return apiRequest<ResumeVersion>(`/api/resumes/${versionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a resume version.
   */
  delete: (versionId: number): Promise<void> => {
    return apiRequest<void>(`/api/resumes/${versionId}`, {
      method: "DELETE",
    });
  },

  /**
   * List all resume versions for a job.
   */
  listVersionsByJob: (jobId: number): Promise<ResumeVersion[]> => {
    const queryParams = new URLSearchParams({
      job_id: jobId.toString(),
      history: "1",
    });
    return apiRequest<ResumeVersion[]>(`/api/resumes?${queryParams.toString()}`);
  },

  /**
   * List all resume versions for a job given a version ID.
   * Uses the version to find the job, then returns all versions.
   */
  listVersions: (versionId: number): Promise<ResumeVersion[]> => {
    return apiRequest<ResumeVersion[]>(`/api/resumes/${versionId}/versions`);
  },

  /**
   * Get a specific resume version by ID (same as get, for backwards compatibility).
   */
  getVersion: async (_jobId: number, versionId: number): Promise<ResumeVersion | null> => {
    try {
      return await resumesAPI.get(versionId);
    } catch {
      return null;
    }
  },

  /**
   * Create a new resume version under the same job as an existing version.
   */
  createVersion: (existingVersionId: number, data: ResumeVersionCreateInput): Promise<ResumeVersion> => {
    return apiRequest<ResumeVersion>(`/api/resumes/${existingVersionId}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Pin a resume version as the current resume.
   */
  pinVersion: (versionId: number): Promise<ResumeVersion> => {
    return resumesAPI.update(versionId, { is_pinned: true });
  },

  /**
   * Unpin a resume version.
   */
  unpinVersion: async (versionId: number): Promise<ResumeVersion> => {
    return resumesAPI.update(versionId, { is_pinned: false });
  },

  /**
   * @deprecated PDF generation is now done client-side.
   * Use `usePdfGeneration` hook from `@/lib/hooks/usePdfGeneration` instead.
   * Or use the `ResumePDFPreview` component for inline preview.
   */
  downloadPDF: async (_jobId: number, _versionId: number): Promise<Blob> => {
    throw new Error(
      "PDF generation is now done client-side. " +
      "Use the usePdfGeneration hook or ResumePDFPreview component."
    );
  },

  /**
   * @deprecated PDF generation is now done client-side.
   * Use `usePdfGeneration` hook from `@/lib/hooks/usePdfGeneration` instead.
   */
  previewPDFDraft: async (_jobId: number, _request: ResumePreviewRequest): Promise<Blob> => {
    throw new Error(
      "PDF generation is now done client-side. " +
      "Use the usePdfGeneration hook or ResumePDFPreview component."
    );
  },

  /**
   * @deprecated PDF generation is now done client-side.
   * Use `usePdfGeneration` hook from `@/lib/hooks/usePdfGeneration` instead.
   */
  previewPDF: async (
    _jobId: number,
    _versionId: number,
    _resumeData?: ResumeData,
    _templateName?: string
  ): Promise<Blob> => {
    throw new Error(
      "PDF generation is now done client-side. " +
      "Use the usePdfGeneration hook or ResumePDFPreview component."
    );
  },

  /**
   * Compare two resume versions.
   * Fetches both versions and returns them for client-side comparison.
   */
  compareVersions: async (
    _jobId: number,
    version1Id: number,
    version2Id: number
  ): Promise<{ version1: ResumeVersion; version2: ResumeVersion }> => {
    const [version1, version2] = await Promise.all([
      resumesAPI.get(version1Id),
      resumesAPI.get(version2Id),
    ]);
    return { version1, version2 };
  },
};
