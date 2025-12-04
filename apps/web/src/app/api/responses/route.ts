/**
 * Responses API - List and Create
 *
 * GET  /api/responses?source=manual&ignore=false - List responses with optional filters
 * POST /api/responses - Create a new response
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import type { ResponseSource } from "@resume/database/types";
import {
  responseCreateSchema,
  responseSourceValues,
} from "./_lib/schema/response.schema";

/**
 * GET /api/responses
 * List responses with optional filters.
 *
 * Query Parameters:
 * - source (optional): Filter by source ("manual" or "application")
 * - ignore (optional): Filter by ignore flag (true/false)
 * - job_id (optional): Filter by job ID
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;

    // Parse source filter (optional)
    const sourceFilter = searchParams.get("source") as ResponseSource | null;
    if (
      sourceFilter &&
      !responseSourceValues.includes(
        sourceFilter as (typeof responseSourceValues)[number]
      )
    ) {
      return NextResponse.json(
        {
          error: `Invalid source filter. Must be one of: ${responseSourceValues.join(", ")}`,
        },
        { status: 400 }
      );
    }

    // Parse ignore filter (optional)
    const ignoreParam = searchParams.get("ignore");
    const ignoreFilter =
      ignoreParam === "true" ? true : ignoreParam === "false" ? false : null;

    // Parse job_id filter (optional)
    const jobIdParam = searchParams.get("job_id");
    let jobIdFilter: number | null = null;
    if (jobIdParam) {
      jobIdFilter = parseInt(jobIdParam, 10);
      if (isNaN(jobIdFilter)) {
        return NextResponse.json(
          { error: "Invalid job_id parameter" },
          { status: 400 }
        );
      }
    }

    const supabase = await getSupabaseServerClient();

    // Build the query
    let query = supabase.from("responses").select("*");

    // Apply filters
    if (sourceFilter) {
      query = query.eq("source", sourceFilter);
    }
    if (ignoreFilter !== null) {
      query = query.eq("ignore", ignoreFilter);
    }
    if (jobIdFilter !== null) {
      query = query.eq("job_id", jobIdFilter);
    }

    // Order by created_at descending
    query = query.order("created_at", { ascending: false });

    const { data: responses, error } = await query;

    if (error) {
      console.error("Failed to list responses:", error);
      return NextResponse.json(
        { error: "Failed to list responses", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(responses);
  } catch (error) {
    console.error("Unexpected error listing responses:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/responses
 * Create a new response.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // Validate request body
    const parseResult = responseCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    // If job_id is provided, verify job exists
    if (parseResult.data.job_id) {
      const { data: job, error: jobError } = await supabase
        .from("jobs")
        .select("id")
        .eq("id", parseResult.data.job_id)
        .single();

      if (jobError || !job) {
        return NextResponse.json({ error: "Job not found" }, { status: 404 });
      }
    }

    const { data: response, error } = await supabase
      .from("responses")
      .insert({
        job_id: parseResult.data.job_id ?? null,
        source: parseResult.data.source,
        prompt: parseResult.data.prompt,
        response: parseResult.data.response,
        ignore: parseResult.data.ignore ?? false,
        locked: parseResult.data.locked ?? false,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create response:", error);
      return NextResponse.json(
        { error: "Failed to create response", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(response, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating response:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

