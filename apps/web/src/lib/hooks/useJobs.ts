"use client";

import { useQuery } from "@tanstack/react-query";

import { jobsAPI } from "@/lib/api/jobs";
import type { JobStatus } from "@resume/database/types";

interface UseJobsParams {
  userId: number;
  statusFilter?: JobStatus | null;
  favoriteOnly?: boolean;
  skip?: number;
  limit?: number;
}

/**
 * Hook to fetch list of jobs for a user with pagination.
 */
export function useJobs(params: UseJobsParams) {
  return useQuery({
    queryKey: [
      "jobs",
      params.userId,
      params.statusFilter,
      params.favoriteOnly,
      params.skip,
      params.limit,
    ],
    queryFn: () =>
      jobsAPI.list({
        user_id: params.userId,
        status_filter: params.statusFilter ?? undefined,
        favorite_only: params.favoriteOnly,
        skip: params.skip,
        limit: params.limit,
      }),
    enabled: params.userId > 0,
  });
}

/**
 * Hook to fetch a single job by ID.
 */
export function useJob(jobId: number) {
  return useQuery({
    queryKey: ["jobs", jobId],
    queryFn: () => jobsAPI.get(jobId),
    enabled: !!jobId,
  });
}
