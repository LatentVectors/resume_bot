/**
 * Notes API - List and Create
 *
 * GET  /api/notes?job_id=1 - List notes for a job
 * POST /api/notes - Create a new note
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { noteCreateSchema } from "./_lib/schema/note.schema";

/**
 * GET /api/notes
 * List notes for a job.
 *
 * Query Parameters:
 * - job_id (required): Filter by job ID
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;

    // Parse job_id (required)
    const jobIdParam = searchParams.get("job_id");
    if (!jobIdParam) {
      return NextResponse.json(
        { error: "job_id query parameter is required" },
        { status: 400 }
      );
    }
    const jobId = parseInt(jobIdParam, 10);
    if (isNaN(jobId)) {
      return NextResponse.json(
        { error: "Invalid job_id parameter" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: notes, error } = await supabase
      .from("notes")
      .select("*")
      .eq("job_id", jobId)
      .order("created_at", { ascending: false });

    if (error) {
      console.error("Failed to list notes:", error);
      return NextResponse.json(
        { error: "Failed to list notes", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(notes);
  } catch (error) {
    console.error("Unexpected error listing notes:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/notes
 * Create a new note.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = noteCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Verify job exists
    const { data: job, error: jobError } = await supabase
      .from("jobs")
      .select("id")
      .eq("id", parseResult.data.job_id)
      .single();

    if (jobError || !job) {
      return NextResponse.json({ error: "Job not found" }, { status: 404 });
    }

    const { data: note, error } = await supabase
      .from("notes")
      .insert({
        job_id: parseResult.data.job_id,
        content: parseResult.data.content,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create note:", error);
      return NextResponse.json(
        { error: "Failed to create note", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(note, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating note:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

