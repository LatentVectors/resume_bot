/**
 * Cover letters API client endpoints.
 *
 * Note: The cover_letters table has been consolidated into cover_letter_versions.
 * The "current" cover letter for a job is the version with is_pinned=true.
 * All operations now work with cover_letter_versions directly.
 */

import { apiRequest } from "./client";
import type { CoverLetterVersion } from "@resume/database/types";

/**
 * Cover letter data type for cover letter JSON content.
 */
export interface CoverLetterData {
  greeting?: string;
  opening_paragraph?: string;
  body_paragraphs?: string[];
  closing_paragraph?: string;
  signature?: string;
  [key: string]: unknown;
}

/**
 * Cover letter preview request type.
 */
export interface CoverLetterPreviewRequest {
  cover_letter_data: CoverLetterData;
  template_name: string;
}

/**
 * Input for creating a cover letter version.
 */
export interface CoverLetterVersionCreateInput {
  job_id: number;
  cover_letter_json: string;
  template_name?: string;
  event_type: "generate" | "save" | "reset";
  parent_version_id?: number | null;
  created_by_user_id: number;
  is_pinned?: boolean;
}

/**
 * Input for updating a cover letter version.
 */
export interface CoverLetterVersionUpdateInput {
  cover_letter_json?: string;
  template_name?: string;
  is_pinned?: boolean;
  locked?: boolean;
}

export const coverLettersAPI = {
  /**
   * List pinned cover letter versions for a job (the "current" cover letters).
   * In the consolidated model, there's at most one pinned version per job.
   */
  listByJob: (jobId: number): Promise<CoverLetterVersion[]> => {
    const queryParams = new URLSearchParams({
      job_id: jobId.toString(),
    });
    return apiRequest<CoverLetterVersion[]>(`/api/cover-letters?${queryParams.toString()}`);
  },

  /**
   * Get current (pinned) cover letter for a job.
   * Returns the pinned version for the job.
   * @throws Error if no pinned cover letter exists for the job
   */
  getCurrent: async (jobId: number): Promise<CoverLetterVersion> => {
    const coverLetters = await coverLettersAPI.listByJob(jobId);
    if (coverLetters.length === 0) {
      throw new Error("No cover letter found for this job");
    }
    return coverLetters[0];
  },

  /**
   * Get current (pinned) cover letter for a job, or null if none exists.
   */
  getCurrentOrNull: async (jobId: number): Promise<CoverLetterVersion | null> => {
    const coverLetters = await coverLettersAPI.listByJob(jobId);
    return coverLetters.length > 0 ? coverLetters[0] : null;
  },

  /**
   * Get a specific cover letter version by ID.
   */
  get: (versionId: number): Promise<CoverLetterVersion> => {
    return apiRequest<CoverLetterVersion>(`/api/cover-letters/${versionId}`);
  },

  /**
   * Create a new cover letter version.
   * If is_pinned is true, will unpin any existing pinned version for the job.
   */
  create: (data: CoverLetterVersionCreateInput): Promise<CoverLetterVersion> => {
    return apiRequest<CoverLetterVersion>(`/api/cover-letters`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Update a cover letter version.
   * If is_pinned is set to true, will unpin any existing pinned version for the job.
   */
  update: (versionId: number, data: CoverLetterVersionUpdateInput): Promise<CoverLetterVersion> => {
    return apiRequest<CoverLetterVersion>(`/api/cover-letters/${versionId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a cover letter version.
   */
  delete: (versionId: number): Promise<void> => {
    return apiRequest<void>(`/api/cover-letters/${versionId}`, {
      method: "DELETE",
    });
  },

  /**
   * List all cover letter versions for a job.
   * First gets the pinned version, then fetches all versions for that job.
   * Returns empty array if no versions exist for the job.
   */
  listVersionsByJob: async (jobId: number): Promise<CoverLetterVersion[]> => {
    const pinned = await coverLettersAPI.getCurrentOrNull(jobId);
    if (!pinned) {
      return [];
    }
    return coverLettersAPI.listVersions(pinned.id);
  },

  /**
   * List all cover letter versions for a job given a version ID.
   * Uses the version to find the job, then returns all versions.
   */
  listVersions: (versionId: number): Promise<CoverLetterVersion[]> => {
    return apiRequest<CoverLetterVersion[]>(`/api/cover-letters/${versionId}/versions`);
  },

  /**
   * Get a specific cover letter version by ID (same as get, for backwards compatibility).
   */
  getVersion: async (_jobId: number, versionId: number): Promise<CoverLetterVersion | null> => {
    try {
      return await coverLettersAPI.get(versionId);
    } catch {
      return null;
    }
  },

  /**
   * Create a new cover letter version under the same job as an existing version.
   */
  createVersion: (existingVersionId: number, data: CoverLetterVersionCreateInput): Promise<CoverLetterVersion> => {
    return apiRequest<CoverLetterVersion>(`/api/cover-letters/${existingVersionId}/versions`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Pin a cover letter version as the current cover letter.
   * Sets is_pinned=true on the specified version.
   */
  pinVersion: async (_existingVersionId: number, versionId: number): Promise<CoverLetterVersion> => {
    return coverLettersAPI.update(versionId, { is_pinned: true });
  },

  /**
   * Unpin a cover letter version.
   */
  unpinVersion: async (versionId: number): Promise<CoverLetterVersion> => {
    return coverLettersAPI.update(versionId, { is_pinned: false });
  },

  /**
   * Preview cover letter PDF from draft data (no version required).
   * Note: PDF generation is now done client-side.
   */
  previewPDFDraft: async (_jobId: number, _request: CoverLetterPreviewRequest): Promise<Blob> => {
    throw new Error("PDF generation is now done client-side. Use the PDF preview component.");
  },

  /**
   * Download cover letter PDF for a specific version.
   * Note: PDF generation is now done client-side.
   */
  downloadPDF: async (_jobId: number, _versionId: number): Promise<Blob> => {
    throw new Error("PDF generation is now done client-side. Use the PDF preview component.");
  },

  /**
   * Compare two cover letter versions.
   * Fetches both versions and returns them for client-side comparison.
   */
  compareVersions: async (
    _jobId: number,
    version1Id: number,
    version2Id: number
  ): Promise<{ version1: CoverLetterVersion; version2: CoverLetterVersion }> => {
    const [version1, version2] = await Promise.all([
      coverLettersAPI.get(version1Id),
      coverLettersAPI.get(version2Id),
    ]);
    return { version1, version2 };
  },
};
