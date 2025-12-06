/**
 * Experiences API client endpoints.
 */

import { apiRequest } from "./client";
import type {
  Experience,
  ExperienceInsert,
  ExperienceUpdate,
  Achievement,
  AchievementInsert,
  AchievementUpdate,
  ExperienceProposal,
  ExperienceProposalInsert,
} from "@resume/database/types";

export const experiencesAPI = {
  /**
   * List all experiences for a user.
   */
  list: (userId: number): Promise<Experience[]> => {
    const queryParams = new URLSearchParams({
      user_id: userId.toString(),
    });
    return apiRequest<Experience[]>(`/api/experiences?${queryParams.toString()}`);
  },

  /**
   * Get a specific experience.
   */
  get: (experienceId: number): Promise<Experience> => {
    return apiRequest<Experience>(`/api/experiences/${experienceId}`);
  },

  /**
   * Create a new experience.
   */
  create: (params: { user_id: number; data: Omit<ExperienceInsert, "user_id"> }): Promise<Experience> => {
    const queryParams = new URLSearchParams({
      user_id: params.user_id.toString(),
    });
    return apiRequest<Experience>(`/api/experiences?${queryParams.toString()}`, {
      method: "POST",
      body: JSON.stringify(params.data),
    });
  },

  /**
   * Update an experience.
   */
  update: (experienceId: number, data: ExperienceUpdate): Promise<Experience> => {
    return apiRequest<Experience>(`/api/experiences/${experienceId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete an experience.
   */
  delete: (experienceId: number): Promise<void> => {
    return apiRequest<void>(`/api/experiences/${experienceId}`, {
      method: "DELETE",
    });
  },

  /**
   * List all achievements for an experience.
   */
  listAchievements: (experienceId: number): Promise<Achievement[]> => {
    const queryParams = new URLSearchParams({
      experience_id: experienceId.toString(),
    });
    return apiRequest<Achievement[]>(`/api/achievements?${queryParams.toString()}`);
  },

  /**
   * Create a new achievement.
   */
  createAchievement: (experienceId: number, data: Omit<AchievementInsert, "experience_id">): Promise<Achievement> => {
    const queryParams = new URLSearchParams({
      experience_id: experienceId.toString(),
    });
    return apiRequest<Achievement>(`/api/achievements?${queryParams.toString()}`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Update an achievement.
   */
  updateAchievement: (achievementId: number, data: AchievementUpdate): Promise<Achievement> => {
    return apiRequest<Achievement>(`/api/achievements/${achievementId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete an achievement.
   */
  deleteAchievement: (achievementId: number): Promise<void> => {
    return apiRequest<void>(`/api/achievements/${achievementId}`, {
      method: "DELETE",
    });
  },

  /**
   * List all proposals for an experience within a session.
   */
  listProposals: (experienceId: number, sessionId: number): Promise<ExperienceProposal[]> => {
    const queryParams = new URLSearchParams({
      session_id: sessionId.toString(),
      experience_id: experienceId.toString(),
    });
    return apiRequest<ExperienceProposal[]>(`/api/experience-proposals?${queryParams.toString()}`);
  },

  /**
   * Create a new proposal.
   */
  createProposal: (data: ExperienceProposalInsert): Promise<ExperienceProposal> => {
    return apiRequest<ExperienceProposal>("/api/experience-proposals", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  /**
   * Accept a proposal.
   */
  acceptProposal: (proposalId: number): Promise<ExperienceProposal> => {
    return apiRequest<ExperienceProposal>(`/api/experience-proposals/${proposalId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "accepted" }),
    });
  },

  /**
   * Reject a proposal.
   */
  rejectProposal: (proposalId: number): Promise<ExperienceProposal> => {
    return apiRequest<ExperienceProposal>(`/api/experience-proposals/${proposalId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "rejected" }),
    });
  },

  /**
   * Delete a proposal.
   */
  deleteProposal: (proposalId: number): Promise<void> => {
    return apiRequest<void>(`/api/experience-proposals/${proposalId}`, {
      method: "DELETE",
    });
  },
};
