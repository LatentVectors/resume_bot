"use client";

import { useState } from "react";
import { Edit2, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";
import { useNotes } from "@/lib/hooks/useNotes";
import { useCreateNote, useUpdateNote, useDeleteNote } from "@/lib/hooks/useNoteMutations";
import type { NoteResponse } from "@/lib/api/notes";
import type { components } from "@/types/api";

type JobResponse = components["schemas"]["JobResponse"];

interface NotesTabProps {
  jobId: number;
  job: JobResponse;
}

export function NotesTab({ jobId }: NotesTabProps) {
  const [newNote, setNewNote] = useState("");
  const [editingNoteId, setEditingNoteId] = useState<number | null>(null);
  const [editingContent, setEditingContent] = useState("");
  const [originalEditingContent, setOriginalEditingContent] = useState("");
  const [expandedNoteIds, setExpandedNoteIds] = useState<Set<number>>(new Set());
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [noteToDelete, setNoteToDelete] = useState<NoteResponse | null>(null);

  const { data: notes = [], isLoading } = useNotes(jobId);
  const createNote = useCreateNote();
  const updateNote = useUpdateNote();
  const deleteNote = useDeleteNote();

  // Sort notes by created_at descending (newest first)
  const sortedNotes = [...notes].sort(
    (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
  );

  const handleAddNote = async () => {
    if (!newNote.trim()) return;

    try {
      await createNote.mutateAsync({
        jobId,
        data: { content: newNote.trim() },
      });
      setNewNote("");
    } catch (error) {
      console.error("Failed to create note:", error);
    }
  };

  const handleStartEdit = (note: NoteResponse) => {
    setEditingNoteId(note.id);
    setEditingContent(note.content);
    setOriginalEditingContent(note.content);
  };

  const handleCancelEdit = () => {
    setEditingNoteId(null);
    setEditingContent("");
    setOriginalEditingContent("");
  };

  const handleSaveEdit = async () => {
    if (!editingNoteId || !editingContent.trim()) return;

    try {
      await updateNote.mutateAsync({
        jobId,
        noteId: editingNoteId,
        data: { content: editingContent.trim() },
      });
      setEditingNoteId(null);
      setEditingContent("");
      setOriginalEditingContent("");
    } catch (error) {
      console.error("Failed to update note:", error);
    }
  };

  const handleDeleteClick = (note: NoteResponse) => {
    setNoteToDelete(note);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!noteToDelete) return;

    try {
      await deleteNote.mutateAsync({
        jobId,
        noteId: noteToDelete.id,
      });
      setDeleteDialogOpen(false);
      setNoteToDelete(null);
    } catch (error) {
      console.error("Failed to delete note:", error);
    }
  };

  const toggleNoteExpansion = (noteId: number) => {
    setExpandedNoteIds((prev) => {
      const next = new Set(prev);
      if (next.has(noteId)) {
        next.delete(noteId);
      } else {
        next.add(noteId);
      }
      return next;
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString(undefined, {
      month: "long",
      day: "numeric",
      year: "numeric",
    });
  };

  const truncateContent = (content: string, maxLength: number = 500) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + "...";
  };

  const isNewNoteDirty = newNote.trim().length > 0;
  const isEditingDirty =
    editingNoteId !== null &&
    editingContent.trim() !== "" &&
    editingContent.trim() !== originalEditingContent.trim();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Notes</h2>
          <p className="text-muted-foreground">
            Add personal notes about this job application
          </p>
        </div>
      </div>

      {/* Two-Column Layout: 60% left, 40% right */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[60%_40%]">
        {/* Left Column - Notes List (60% width) */}
        <div className="space-y-4 lg:pr-6 lg:border-r max-h-[calc(100vh-200px)] overflow-y-auto">
          {isLoading ? (
            <div className="text-muted-foreground">Loading notes...</div>
          ) : sortedNotes.length === 0 ? (
            <div className="text-muted-foreground">
              No notes yet. Add your first note in the form on the right.
            </div>
          ) : (
            sortedNotes.map((note) => (
              <Card key={note.id}>
                <CardContent className="pt-6">
                  {editingNoteId === note.id ? (
                    // Edit Mode
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-muted-foreground">
                          {formatDate(note.created_at)}
                        </span>
                        <div className="flex gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleCancelEdit}
                            disabled={updateNote.isPending}
                          >
                            Discard
                          </Button>
                          <Button
                            size="sm"
                            onClick={handleSaveEdit}
                            disabled={!isEditingDirty || updateNote.isPending}
                          >
                            {updateNote.isPending ? "Saving..." : "Save"}
                          </Button>
                        </div>
                      </div>
                      <Textarea
                        value={editingContent}
                        onChange={(e) => setEditingContent(e.target.value)}
                        className="min-h-[200px]"
                        autoFocus
                      />
                    </div>
                  ) : (
                    // View Mode
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium">
                          {formatDate(note.created_at)}
                        </span>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleStartEdit(note)}
                            disabled={editingNoteId !== null}
                          >
                            <Edit2 className="size-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDeleteClick(note)}
                            disabled={editingNoteId !== null}
                            className="text-destructive hover:text-destructive hover:bg-destructive/10"
                          >
                            <Trash2 className="size-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="whitespace-pre-wrap text-sm">
                        {expandedNoteIds.has(note.id) || note.content.length <= 500
                          ? note.content
                          : truncateContent(note.content)}
                      </div>
                      {note.content.length > 500 && (
                        <button
                          onClick={() => toggleNoteExpansion(note.id)}
                          className="text-sm text-primary hover:underline"
                        >
                          {expandedNoteIds.has(note.id) ? "Show less" : "Show more"}
                        </button>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Right Column - New Note Form (40% width, sticky) */}
        <div className="lg:sticky lg:top-20">
          <div className="space-y-4">
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setNewNote("")}
                disabled={!isNewNoteDirty || createNote.isPending}
              >
                Discard
              </Button>
              <Button
                onClick={handleAddNote}
                disabled={!isNewNoteDirty || createNote.isPending}
              >
                {createNote.isPending ? "Saving..." : "Save"}
              </Button>
            </div>
            <Textarea
              value={newNote}
              onChange={(e) => setNewNote(e.target.value)}
              placeholder="add new note here..."
              className="h-[calc(100vh-300px)] min-h-[200px] max-h-[600px] resize-none"
            />
          </div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <DeleteConfirmationDialog
        open={deleteDialogOpen}
        onOpenChange={setDeleteDialogOpen}
        onConfirm={handleConfirmDelete}
        itemName={noteToDelete?.content.substring(0, 50) || ""}
        itemType="note"
        isDeleting={deleteNote.isPending}
      />
    </div>
  );
}
