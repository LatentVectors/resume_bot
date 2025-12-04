/**
 * Jobs API - List and Create
 *
 * GET  /api/jobs?user_id=1&status_filter=Saved&favorite_only=false&skip=0&limit=50 - List jobs for a user
 * POST /api/jobs?user_id=1 - Create a new job
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";
import type { Job, JobStatus } from "@resume/database/types";
import { jobCreateSchema, jobStatusValues } from "./_lib/schema/job.schema";

/**
 * Response type for the jobs list endpoint.
 */
interface JobsListResponse {
  items: Job[];
  total: number;
  skip: number;
  limit: number;
}

/**
 * GET /api/jobs
 * List jobs for a user with optional filters and pagination.
 *
 * Query Parameters:
 * - user_id (required): User ID
 * - status_filter: Filter by job status
 * - favorite_only: Show only favorites (default: false)
 * - skip: Number of records to skip (default: 0)
 * - limit: Maximum number of records to return (default: 50, max: 1000)
 */
export async function GET(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;

    // Parse user_id (required)
    const userIdParam = searchParams.get("user_id");
    if (!userIdParam) {
      return NextResponse.json(
        { error: "user_id query parameter is required" },
        { status: 400 }
      );
    }
    const userId = parseInt(userIdParam, 10);
    if (isNaN(userId)) {
      return NextResponse.json(
        { error: "Invalid user_id parameter" },
        { status: 400 }
      );
    }

    // Parse status_filter (optional)
    const statusFilter = searchParams.get("status_filter") as JobStatus | null;
    if (statusFilter && !jobStatusValues.includes(statusFilter as typeof jobStatusValues[number])) {
      return NextResponse.json(
        { error: `Invalid status_filter. Must be one of: ${jobStatusValues.join(", ")}` },
        { status: 400 }
      );
    }

    // Parse favorite_only (optional, default: false)
    const favoriteOnlyParam = searchParams.get("favorite_only");
    const favoriteOnly = favoriteOnlyParam === "true";

    // Parse skip (optional, default: 0)
    const skipParam = searchParams.get("skip");
    const skip = skipParam ? parseInt(skipParam, 10) : 0;
    if (isNaN(skip) || skip < 0) {
      return NextResponse.json(
        { error: "Invalid skip parameter. Must be a non-negative integer." },
        { status: 400 }
      );
    }

    // Parse limit (optional, default: 50, max: 1000)
    const limitParam = searchParams.get("limit");
    let limit = limitParam ? parseInt(limitParam, 10) : 50;
    if (isNaN(limit) || limit < 1) {
      return NextResponse.json(
        { error: "Invalid limit parameter. Must be a positive integer." },
        { status: 400 }
      );
    }
    limit = Math.min(limit, 1000); // Cap at 1000

    const supabase = await getSupabaseServerClient();

    // Build the query
    let query = supabase
      .from("jobs")
      .select("*", { count: "exact" })
      .eq("user_id", userId);

    // Apply filters
    if (statusFilter) {
      query = query.eq("status", statusFilter);
    }
    if (favoriteOnly) {
      query = query.eq("is_favorite", true);
    }

    // Apply pagination and ordering
    query = query
      .order("updated_at", { ascending: false })
      .range(skip, skip + limit - 1);

    const { data: jobs, error, count } = await query;

    if (error) {
      console.error("Failed to list jobs:", error);
      return NextResponse.json(
        { error: "Failed to list jobs", details: error.message },
        { status: 500 }
      );
    }

    const response: JobsListResponse = {
      items: jobs || [],
      total: count || 0,
      skip,
      limit,
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error("Unexpected error listing jobs:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

/**
 * POST /api/jobs
 * Create a new job.
 * Requires user_id query parameter.
 */
export async function POST(req: NextRequest) {
  try {
    const searchParams = req.nextUrl.searchParams;
    const userIdParam = searchParams.get("user_id");

    if (!userIdParam) {
      return NextResponse.json(
        { error: "user_id query parameter is required" },
        { status: 400 }
      );
    }

    const userId = parseInt(userIdParam, 10);
    if (isNaN(userId)) {
      return NextResponse.json(
        { error: "Invalid user_id parameter" },
        { status: 400 }
      );
    }

    const body = await req.json();

    // Validate request body
    const parseResult = jobCreateSchema.safeParse(body);
    if (!parseResult.success) {
      return NextResponse.json(
        { error: "Validation failed", details: parseResult.error.flatten() },
        { status: 400 }
      );
    }

    const supabase = await getSupabaseServerClient();

    const { data: job, error } = await supabase
      .from("jobs")
      .insert({
        user_id: userId,
        job_title: parseResult.data.job_title ?? null,
        company_name: parseResult.data.company_name ?? null,
        job_description: parseResult.data.job_description,
        is_favorite: parseResult.data.is_favorite ?? false,
        status: parseResult.data.status ?? "Saved",
        has_resume: false,
        has_cover_letter: false,
      })
      .select()
      .single();

    if (error) {
      console.error("Failed to create job:", error);
      return NextResponse.json(
        { error: "Failed to create job", details: error.message },
        { status: 500 }
      );
    }

    return NextResponse.json(job, { status: 201 });
  } catch (error) {
    console.error("Unexpected error creating job:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

