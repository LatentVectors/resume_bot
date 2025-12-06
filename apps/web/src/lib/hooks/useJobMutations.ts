"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { jobsAPI } from "@/lib/api/jobs";
import type { JobInsert, JobUpdate, JobStatus } from "@resume/database/types";

/**
 * Hook to create a new job.
 */
export function useCreateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { user_id: number; data: Omit<JobInsert, "user_id"> }) =>
      jobsAPI.create(params),
    onSuccess: () => {
      // Invalidate jobs list queries
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

/**
 * Hook to update a job.
 */
export function useUpdateJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { jobId: number; data: JobUpdate }) =>
      jobsAPI.update(params.jobId, params.data),
    onSuccess: (_, variables) => {
      // Invalidate specific job and jobs list
      queryClient.invalidateQueries({ queryKey: ["jobs", variables.jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

/**
 * Hook to delete a job.
 */
export function useDeleteJob() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: number) => jobsAPI.delete(jobId),
    onSuccess: (_, jobId) => {
      // Remove from cache and invalidate list
      queryClient.removeQueries({ queryKey: ["jobs", jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

/**
 * Hook to toggle favorite status for a job.
 */
export function useToggleFavorite() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { jobId: number; favorite: boolean }) =>
      jobsAPI.toggleFavorite(params.jobId, params.favorite),
    onSuccess: (_, variables) => {
      // Invalidate specific job and jobs list
      queryClient.invalidateQueries({ queryKey: ["jobs", variables.jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

/**
 * Hook to update job status.
 */
export function useUpdateJobStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { jobId: number; status: JobStatus }) =>
      jobsAPI.updateStatus(params.jobId, params.status),
    onSuccess: (_, variables) => {
      // Invalidate specific job and jobs list
      queryClient.invalidateQueries({ queryKey: ["jobs", variables.jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

/**
 * Hook to mark a job as applied.
 */
export function useMarkAsApplied() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobId: number) => jobsAPI.markAsApplied(jobId),
    onSuccess: (_, jobId) => {
      // Invalidate specific job and jobs list
      queryClient.invalidateQueries({ queryKey: ["jobs", jobId] });
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

/**
 * Hook to bulk delete jobs.
 */
export function useBulkDeleteJobs() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (jobIds: number[]) => jobsAPI.bulkDelete(jobIds),
    onSuccess: () => {
      // Invalidate all jobs queries
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
  });
}

