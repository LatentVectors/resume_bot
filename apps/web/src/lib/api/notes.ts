/**
 * Notes API client endpoints.
 */

import { apiRequest } from "./client";
import type { Note, NoteInsert, NoteUpdate } from "@resume/database/types";

export const notesAPI = {
  /**
   * List all notes for a job.
   */
  list: (jobId: number): Promise<Note[]> => {
    const queryParams = new URLSearchParams({
      job_id: jobId.toString(),
    });
    return apiRequest<Note[]>(`/api/notes?${queryParams.toString()}`);
  },

  /**
   * Get a specific note.
   */
  get: (noteId: number): Promise<Note> => {
    return apiRequest<Note>(`/api/notes/${noteId}`);
  },

  /**
   * Create a new note for a job.
   */
  create: (jobId: number, data: Omit<NoteInsert, "job_id">): Promise<Note> => {
    return apiRequest<Note>(`/api/notes`, {
      method: "POST",
      body: JSON.stringify({ ...data, job_id: jobId }),
    });
  },

  /**
   * Update a note.
   */
  update: (_jobId: number, noteId: number, data: NoteUpdate): Promise<Note> => {
    return apiRequest<Note>(`/api/notes/${noteId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a note.
   */
  delete: (_jobId: number, noteId: number): Promise<void> => {
    return apiRequest<void>(`/api/notes/${noteId}`, {
      method: "DELETE",
    });
  },
};
