"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { educationAPI } from "@/lib/api/education";
import type { EducationInsert, EducationUpdate } from "@resume/database/types";

/**
 * Hook to create a new education entry.
 */
export function useCreateEducation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { user_id: number; data: Omit<EducationInsert, "user_id"> }) =>
      educationAPI.create(params),
    onSuccess: (_, variables) => {
      // Invalidate education list queries
      queryClient.invalidateQueries({ queryKey: ["education", variables.user_id] });
    },
  });
}

/**
 * Hook to update an education entry.
 */
export function useUpdateEducation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { educationId: number; data: EducationUpdate }) =>
      educationAPI.update(params.educationId, params.data),
    onSuccess: (data) => {
      // Invalidate specific education and education list
      queryClient.invalidateQueries({ queryKey: ["education", data.id] });
      queryClient.invalidateQueries({ queryKey: ["education", data.user_id] });
    },
  });
}

/**
 * Hook to delete an education entry.
 */
export function useDeleteEducation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (educationId: number) => educationAPI.delete(educationId),
    onSuccess: () => {
      // Invalidate all education queries
      queryClient.invalidateQueries({ queryKey: ["education"] });
    },
  });
}

