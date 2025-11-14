"use client";

import { useState } from "react";
import { Save, Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import type { components } from "@/types/api";

type JobResponse = components["schemas"]["JobResponse"];

interface NotesTabProps {
  jobId: number;
  job: JobResponse;
}

export function NotesTab({ jobId, job }: NotesTabProps) {
  const [newNote, setNewNote] = useState("");

  // TODO: Implement notes API endpoints and hooks
  // Notes are stored as separate Note entities in the database
  // For now, this is a placeholder UI that matches the spec requirements
  // Future: Add API endpoints for listing/creating/updating/deleting notes

  const handleAddNote = async () => {
    if (!newNote.trim()) return;
    
    // TODO: Call API to create note
    // await notesAPI.create({ jobId, content: newNote });
    console.log("Add note:", { jobId, content: newNote });
    setNewNote("");
  };

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

      {/* Add Note Form */}
      <Card>
        <CardHeader>
          <CardTitle>Add Note</CardTitle>
          <CardDescription>
            Keep track of important information, interview questions, or thoughts about this position
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Textarea
            value={newNote}
            onChange={(e) => setNewNote(e.target.value)}
            placeholder="Write a note..."
            className="min-h-[120px]"
          />
          <Button onClick={handleAddNote} disabled={!newNote.trim()}>
            <Plus className="mr-2 size-4" />
            Add Note
          </Button>
        </CardContent>
      </Card>

      {/* Notes List */}
      <Card>
        <CardHeader>
          <CardTitle>Notes</CardTitle>
          <CardDescription>Your notes for this job</CardDescription>
        </CardHeader>
        <CardContent>
          {/* TODO: Display list of notes from API */}
          <div className="text-muted-foreground">
            Notes functionality will be implemented when API endpoints are available.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

