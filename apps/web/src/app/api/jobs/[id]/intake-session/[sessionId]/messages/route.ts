/**
 * Job Intake Session Messages API
 *
 * GET  /api/jobs/[id]/intake-session/[sessionId]/messages?step=2 - Get messages for a step
 * POST /api/jobs/[id]/intake-session/[sessionId]/messages?step=2 - Save messages for a step
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import { chatMessagesSchema } from "../../_lib/schema/intake-session.schema";

type RouteParams = { params: Promise<{ id: string; sessionId: string }> };

/**
 * GET /api/jobs/[id]/intake-session/[sessionId]/messages
 * Get chat messages for an intake session step.
 * Requires step query parameter (2 or 3).
 */
export async function GET(req: NextRequest, { params }: RouteParams) {
  try {
    const { id, sessionId } = await params;
    const jobId = parseInt(id, 10);
    const sessionIdNum = parseInt(sessionId, 10);

    if (isNaN(jobId)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    if (isNaN(sessionIdNum)) {
      return NextResponse.json(
        { error: "Invalid session ID" },
        { status: 400 }
      );
    }

    // Get step from query params
    const searchParams = req.nextUrl.searchParams;
    const stepParam = searchParams.get("step");

    if (!stepParam) {
      return NextResponse.json(
        { error: "step query parameter is required" },
        { status: 400 }
      );
    }

    const step = parseInt(stepParam, 10);
    if (isNaN(step) || step < 2 || step > 3) {
      return NextResponse.json(
        { error: "step must be 2 or 3" },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Verify the intake session exists and belongs to this job
    const { data: session, error: sessionError } = await supabase
      .from("job_intake_sessions")
      .select("id, job_id")
      .eq("id", sessionIdNum)
      .single();

    if (sessionError || !session) {
      return NextResponse.json(
        { error: "Intake session not found" },
        { status: 404 }
      );
    }

    if (session.job_id !== jobId) {
      return NextResponse.json(
        { error: "Intake session does not belong to this job" },
        { status: 404 }
      );
    }

    // Get all chat messages for this step, ordered by created_at
    const { data: chatMessages, error } = await supabase
      .from("job_intake_chat_messages")
      .select("*")
      .eq("session_id", sessionIdNum)
      .eq("step", step)
      .order("created_at", { ascending: true });

    if (error) {
      console.error("Failed to get chat messages:", error);
      return NextResponse.json(
        { error: "Failed to get chat messages", details: error.message },
        { status: 500 }
      );
    }

    // Concatenate all message arrays from records
    const allMessages: Record<string, unknown>[] = [];
    for (const record of chatMessages || []) {
      try {
        // Messages are stored as JSONB
        const messages = record.messages;
        if (Array.isArray(messages)) {
          allMessages.push(...(messages as Record<string, unknown>[]));
        }
      } catch (parseError) {
        console.error(
          `Failed to parse messages JSON for record ${record.id}:`,
          parseError
        );
        continue;
      }
    }

    return NextResponse.json(allMessages);
  } catch (error) {
    console.error("Unexpected error getting chat messages:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/jobs/[id]/intake-session/[sessionId]/messages
 * Save chat messages for an intake session step.
 * Requires step query parameter (2 or 3).
 */
export async function POST(req: NextRequest, { params }: RouteParams) {
  try {
    const { id, sessionId } = await params;
    const jobId = parseInt(id, 10);
    const sessionIdNum = parseInt(sessionId, 10);

    if (isNaN(jobId)) {
      return NextResponse.json({ error: "Invalid job ID" }, { status: 400 });
    }

    if (isNaN(sessionIdNum)) {
      return NextResponse.json(
        { error: "Invalid session ID" },
        { status: 400 }
      );
    }

    // Get step from query params
    const searchParams = req.nextUrl.searchParams;
    const stepParam = searchParams.get("step");

    if (!stepParam) {
      return NextResponse.json(
        { error: "step query parameter is required" },
        { status: 400 }
      );
    }

    const step = parseInt(stepParam, 10);
    if (isNaN(step) || step < 2 || step > 3) {
      return NextResponse.json(
        { error: "step must be 2 or 3" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = chatMessagesSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // Verify the intake session exists and belongs to this job
    const { data: session, error: sessionError } = await supabase
      .from("job_intake_sessions")
      .select("id, job_id")
      .eq("id", sessionIdNum)
      .single();

    if (sessionError || !session) {
      return NextResponse.json(
        { error: "Intake session not found" },
        { status: 404 }
      );
    }

    if (session.job_id !== jobId) {
      return NextResponse.json(
        { error: "Intake session does not belong to this job" },
        { status: 404 }
      );
    }

    // Insert the messages as a new record (append behavior)
    const { error } = await supabase.from("job_intake_chat_messages").insert({
      session_id: sessionIdNum,
      step: step,
      messages: parseResult.data.messages,
    });

    if (error) {
      console.error("Failed to save chat messages:", error);
      return NextResponse.json(
        { error: "Failed to save chat messages", details: error.message },
        { status: 500 }
      );
    }

    return new NextResponse(null, { status: 204 });
  } catch (error) {
    console.error("Unexpected error saving chat messages:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

