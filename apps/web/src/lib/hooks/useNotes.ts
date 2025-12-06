"use client";

import { useQuery } from "@tanstack/react-query";

import { notesAPI } from "@/lib/api/notes";

/**
 * Hook to fetch notes for a job.
 */
export function useNotes(jobId: number) {
  return useQuery({
    queryKey: ["notes", jobId],
    queryFn: () => notesAPI.list(jobId),
    enabled: !!jobId,
  });
}

