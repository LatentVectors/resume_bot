"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { experiencesAPI } from "@/lib/api/experiences";
import type {
  ExperienceInsert,
  ExperienceUpdate,
  AchievementInsert,
  AchievementUpdate,
} from "@resume/database/types";

/**
 * Hook to create a new experience.
 */
export function useCreateExperience() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { user_id: number; data: Omit<ExperienceInsert, "user_id"> }) =>
      experiencesAPI.create(params),
    onSuccess: (_, variables) => {
      // Invalidate experiences list queries
      queryClient.invalidateQueries({ queryKey: ["experiences", variables.user_id] });
    },
  });
}

/**
 * Hook to update an experience.
 */
export function useUpdateExperience() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { experienceId: number; data: ExperienceUpdate }) =>
      experiencesAPI.update(params.experienceId, params.data),
    onSuccess: (data) => {
      // Invalidate specific experience and experiences list
      queryClient.invalidateQueries({ queryKey: ["experiences", data.id] });
      queryClient.invalidateQueries({ queryKey: ["experiences", data.user_id] });
    },
  });
}

/**
 * Hook to delete an experience.
 */
export function useDeleteExperience() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (experienceId: number) => experiencesAPI.delete(experienceId),
    onSuccess: () => {
      // Invalidate all experiences queries
      queryClient.invalidateQueries({ queryKey: ["experiences"] });
    },
  });
}

/**
 * Hook to create a new achievement.
 */
export function useCreateAchievement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { experienceId: number; data: Omit<AchievementInsert, "experience_id"> }) =>
      experiencesAPI.createAchievement(params.experienceId, params.data),
    onSuccess: (data) => {
      // Invalidate achievements list for the experience
      queryClient.invalidateQueries({ queryKey: ["achievements", data.experience_id] });
      // Also invalidate the experience itself to refresh achievements
      queryClient.invalidateQueries({ queryKey: ["experiences", data.experience_id] });
    },
  });
}

/**
 * Hook to update an achievement.
 */
export function useUpdateAchievement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { achievementId: number; data: AchievementUpdate }) =>
      experiencesAPI.updateAchievement(params.achievementId, params.data),
    onSuccess: (data) => {
      // Invalidate achievements list for the experience
      queryClient.invalidateQueries({ queryKey: ["achievements", data.experience_id] });
      // Also invalidate the experience itself
      queryClient.invalidateQueries({ queryKey: ["experiences", data.experience_id] });
    },
  });
}

/**
 * Hook to delete an achievement.
 */
export function useDeleteAchievement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (achievementId: number) => experiencesAPI.deleteAchievement(achievementId),
    onSuccess: () => {
      // Invalidate all achievements queries
      queryClient.invalidateQueries({ queryKey: ["achievements"] });
      // Also invalidate all experiences to refresh achievements
      queryClient.invalidateQueries({ queryKey: ["experiences"] });
    },
  });
}

