"use client";

import { useQuery } from "@tanstack/react-query";

import { usersAPI } from "@/lib/api/users";

/**
 * Hook to fetch user statistics.
 */
export function useUserStats(userId: number | undefined) {
  return useQuery({
    queryKey: ["user", userId, "stats"],
    queryFn: () => usersAPI.getStats(userId!),
    enabled: !!userId,
  });
}

