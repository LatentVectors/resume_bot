"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { usersAPI } from "@/lib/api/users";
import type { UserUpdate } from "@resume/database/types";

/**
 * Hook to update a user.
 */
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { userId: number; data: UserUpdate }) =>
      usersAPI.update(params.userId, params.data),
    onSuccess: (data) => {
      // Invalidate user queries
      queryClient.invalidateQueries({ queryKey: ["user", "current"] });
      queryClient.invalidateQueries({ queryKey: ["user", data.id] });
    },
  });
}

