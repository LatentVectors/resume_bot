"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { coverLettersAPI } from "@/lib/api/cover-letters";
import type { CoverLetterVersionInsert } from "@resume/database/types";

/**
 * Hook to fetch cover letter versions for a job.
 */
export function useCoverLetterVersions(jobId: number) {
  return useQuery({
    queryKey: ["cover-letters", jobId, "versions"],
    queryFn: () => coverLettersAPI.listVersions(jobId),
    enabled: !!jobId,
  });
}

/**
 * Hook to fetch current cover letter for a job.
 */
export function useCurrentCoverLetter(jobId: number) {
  return useQuery({
    queryKey: ["cover-letters", jobId, "current"],
    queryFn: () => coverLettersAPI.getCurrent(jobId),
    enabled: !!jobId,
  });
}

/**
 * Hook to fetch a specific cover letter version.
 */
export function useCoverLetterVersion(jobId: number, versionId: number) {
  return useQuery({
    queryKey: ["cover-letters", jobId, "versions", versionId],
    queryFn: () => coverLettersAPI.getVersion(jobId, versionId),
    enabled: !!jobId && !!versionId,
  });
}

/**
 * Hook to create a new cover letter version.
 */
export function useCreateCoverLetterVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { jobId: number; data: CoverLetterVersionInsert }) =>
      coverLettersAPI.createVersion(params.jobId, params.data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cover-letters", variables.jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs", variables.jobId] });
    },
  });
}

/**
 * Hook to pin a cover letter version.
 */
export function usePinCoverLetterVersion() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { jobId: number; versionId: number }) =>
      coverLettersAPI.pinVersion(params.jobId, params.versionId),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["cover-letters", variables.jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs", variables.jobId] });
    },
  });
}

