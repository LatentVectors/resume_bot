"use client";

import { useQuery } from "@tanstack/react-query";

import { educationAPI } from "@/lib/api/education";

/**
 * Hook to fetch list of education entries for a user.
 */
export function useEducation(userId: number) {
  return useQuery({
    queryKey: ["education", userId],
    queryFn: () => educationAPI.list(userId),
    enabled: !!userId,
  });
}

