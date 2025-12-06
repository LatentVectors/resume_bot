"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { notesAPI } from "@/lib/api/notes";
import type { NoteCreate, NoteUpdate } from "@/lib/api/notes";

/**
 * Hook to create a new note.
 */
export function useCreateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { jobId: number; data: NoteCreate }) =>
      notesAPI.create(params.jobId, params.data),
    onSuccess: (_, variables) => {
      // Invalidate notes list for this job
      queryClient.invalidateQueries({ queryKey: ["notes", variables.jobId] });
    },
  });
}

/**
 * Hook to update a note.
 */
export function useUpdateNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { jobId: number; noteId: number; data: NoteUpdate }) =>
      notesAPI.update(params.jobId, params.noteId, params.data),
    onSuccess: (_, variables) => {
      // Invalidate notes list for this job
      queryClient.invalidateQueries({ queryKey: ["notes", variables.jobId] });
    },
  });
}

/**
 * Hook to delete a note.
 */
export function useDeleteNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { jobId: number; noteId: number }) =>
      notesAPI.delete(params.jobId, params.noteId),
    onSuccess: (_, variables) => {
      // Invalidate notes list for this job
      queryClient.invalidateQueries({ queryKey: ["notes", variables.jobId] });
    },
  });
}

