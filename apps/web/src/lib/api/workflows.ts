/**
 * LangGraph-based workflow API client.
 *
 * These functions call Next.js API routes that proxy to the LangGraph API
 * for running AI agent workflows.
 */

/**
 * Gap analysis response type.
 */
export interface GapAnalysisResponse {
  analysis: string;
}

/**
 * Stakeholder analysis response type.
 */
export interface StakeholderAnalysisResponse {
  analysis: string;
}

/**
 * Experience extraction response type.
 */
export interface ExperienceExtractionResponse {
  suggestions: Array<{
    experience_id: number;
    proposed_changes: Array<{
      field: string;
      original: string;
      proposed: string;
      rationale: string;
    }>;
  }>;
}

/**
 * Job details extraction request type.
 */
export interface JobDetailsExtractionRequest {
  job_description: string;
}

/**
 * Job details extraction response type.
 */
export interface JobDetailsExtractionResponse {
  title: string | null;
  company: string | null;
  confidence: number | null;
}

/**
 * LangGraph-based workflow API client.
 * These functions call Next.js API routes that proxy to the LangGraph API.
 */
export const langgraphWorkflowsAPI = {
  /**
   * Run gap analysis using LangGraph agent.
   */
  gapAnalysis: async (request: { job_description: string; work_experience: string }): Promise<GapAnalysisResponse> => {
    const response = await fetch("/api/workflows/gap-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Gap analysis failed");
    }

    return response.json();
  },

  /**
   * Run stakeholder analysis using LangGraph agent.
   */
  stakeholderAnalysis: async (request: { job_description: string; work_experience: string }): Promise<StakeholderAnalysisResponse> => {
    const response = await fetch("/api/workflows/stakeholder-analysis", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Stakeholder analysis failed");
    }

    return response.json();
  },

  /**
   * Extract experience updates from resume refinement conversation.
   */
  experienceExtraction: async (request: { thread_id: string; work_experience: string }): Promise<ExperienceExtractionResponse> => {
    const response = await fetch("/api/workflows/experience-extraction", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Experience extraction failed");
    }

    return response.json();
  },

  /**
   * Extract job title and company name from job description.
   */
  extractJobDetails: async (request: JobDetailsExtractionRequest): Promise<JobDetailsExtractionResponse> => {
    const response = await fetch("/api/workflows/job-details-extraction", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Job details extraction failed");
    }

    return response.json();
  },
};
