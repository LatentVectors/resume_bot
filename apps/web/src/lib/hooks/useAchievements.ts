"use client";

import { useQuery } from "@tanstack/react-query";

import { experiencesAPI } from "@/lib/api/experiences";

/**
 * Hook to fetch list of achievements for an experience.
 */
export function useAchievements(experienceId: number) {
  return useQuery({
    queryKey: ["achievements", experienceId],
    queryFn: () => experiencesAPI.listAchievements(experienceId),
    enabled: !!experienceId,
  });
}

