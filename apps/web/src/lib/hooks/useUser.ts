"use client";

import { useQuery } from "@tanstack/react-query";
import { useEffect } from "react";

import { usersAPI } from "@/lib/api/users";
import { useUserStore } from "@/lib/store/user";

/**
 * Hook to fetch current user and store in Zustand.
 * This is used for single-user authentication model.
 */
export function useCurrentUser() {
  const setUser = useUserStore((state) => state.setUser);
  const clearUser = useUserStore((state) => state.clearUser);

  const query = useQuery({
    queryKey: ["user", "current"],
    queryFn: () => usersAPI.getCurrent(),
    retry: false, // Don't retry if user fetch fails
  });

  // Sync query data to Zustand store
  useEffect(() => {
    if (query.data) {
      setUser(query.data);
    } else if (query.isError) {
      clearUser();
    }
  }, [query.data, query.isError, setUser, clearUser]);

  return query;
}

