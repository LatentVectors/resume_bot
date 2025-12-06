"use client";

import { useQuery } from "@tanstack/react-query";

import { experiencesAPI } from "@/lib/api/experiences";

/**
 * Hook to fetch list of experiences for a user.
 */
export function useExperiences(userId: number) {
  return useQuery({
    queryKey: ["experiences", userId],
    queryFn: () => experiencesAPI.list(userId),
    enabled: !!userId,
  });
}

/**
 * Hook to fetch a single experience by ID.
 */
export function useExperience(experienceId: number) {
  return useQuery({
    queryKey: ["experiences", experienceId],
    queryFn: () => experiencesAPI.get(experienceId),
    enabled: !!experienceId,
  });
}

