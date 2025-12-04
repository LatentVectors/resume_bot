/**
 * Messages API - List and Create
 *
 * GET  /api/messages?job_id=1 - List messages for a job
 * POST /api/messages - Create a new message
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { messageCreateSchema } from "./_lib/schema/message.schema";

/**
 * GET /api/messages
 * List messages for a job.
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

    const { data: messages, error } = await supabase
      .from("messages")
      .select("*")
      .eq("job_id", jobId)
      .order("created_at", { ascending: false });

    if (error) {
      console.error("Failed to list messages:", error);
      return NextResponse.json(
        { error: "Failed to list messages", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(messages);
  } catch (error) {
    console.error("Unexpected error listing messages:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/messages
 * Create a new message.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = messageCreateSchema.safeParse(body);
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
      return NextResponse.json(
        { error: "Job not found" },
        { status: 404 }
      );
    }

    const { data: message, error } = await supabase
      .from("messages")
      .insert({
        job_id: parseResult.data.job_id,
        channel: parseResult.data.channel,
        body: parseResult.data.body,
        sent_at: parseResult.data.sent_at ?? null,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create message:", error);
      return NextResponse.json(
        { error: "Failed to create message", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(message, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating message:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

