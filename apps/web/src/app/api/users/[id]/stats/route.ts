/**
 * User Stats API
 *
 * GET /api/users/[id]/stats - Get statistics for a user's job applications
 */

import { NextRequest, NextResponse } from "next/server";
import { getSupabaseServerClient } from "@resume/database/server";

type RouteParams = { params: Promise<{ id: string }> };

/**
 * GET /api/users/[id]/stats
 * Get statistics for a user's job applications.
 *
 * Returns counts for:
 * - jobs_applied_7_days: Jobs applied in the last 7 days (based on applied_at)
 * - jobs_applied_30_days: Jobs applied in the last 30 days (based on applied_at)
 * - total_jobs_saved: Jobs with status "Saved"
 * - total_jobs_applied: Jobs that have been applied to (have applied_at set)
 * - total_interviews: Jobs with status "Interviewing"
 * - total_offers: Jobs with status "Hired"
 * - total_favorites: Jobs marked as favorite
 * - success_rate: Percentage of applied jobs that resulted in offers
 *
 * Note: A job is considered "applied" if it has an applied_at timestamp,
 * regardless of its current status. This ensures that jobs which have
 * progressed to "Interviewing", "Not Selected", etc. are still counted
 * as applied jobs.
 */
export async function GET(_req: NextRequest, { params }: RouteParams) {
  try {
    const { id } = await params;
    const userId = parseInt(id, 10);

    if (isNaN(userId)) {
      return NextResponse.json({ error: "Invalid user ID" }, { status: 400 });
    }

    const supabase = await getSupabaseServerClient();

    // Get all jobs for this user
    const { data: jobs, error } = await supabase
      .from("jobs")
      .select("status, applied_at, is_favorite")
      .eq("user_id", userId);

    if (error) {
      console.error("Failed to fetch jobs for stats:", error);
      return NextResponse.json(
        { error: "Failed to fetch stats", details: error.message },
        { status: 500 }
      );
    }

    const now = new Date();
    const sevenDaysAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
    const thirtyDaysAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);

    // Calculate stats
    let jobsApplied7Days = 0;
    let jobsApplied30Days = 0;
    let totalJobsSaved = 0;
    let totalJobsApplied = 0;
    let totalInterviews = 0;
    let totalOffers = 0;
    let totalFavorites = 0;

    for (const job of jobs || []) {
      // Count jobs with applied_at set (these are "applied" jobs regardless of current status)
      if (job.applied_at) {
        totalJobsApplied++;

        const appliedDate = new Date(job.applied_at);
        if (appliedDate >= sevenDaysAgo) {
          jobsApplied7Days++;
        }
        if (appliedDate >= thirtyDaysAgo) {
          jobsApplied30Days++;
        }
      }

      // Count by current status
      if (job.status === "Saved") {
        totalJobsSaved++;
      }
      if (job.status === "Interviewing") {
        totalInterviews++;
      }
      if (job.status === "Hired") {
        totalOffers++;
      }

      // Count favorites
      if (job.is_favorite) {
        totalFavorites++;
      }
    }

    // Calculate success rate (offers / applied jobs)
    const successRate =
      totalJobsApplied > 0
        ? Math.round((totalOffers / totalJobsApplied) * 100 * 10) / 10
        : null;

    return NextResponse.json({
      jobs_applied_7_days: jobsApplied7Days,
      jobs_applied_30_days: jobsApplied30Days,
      total_jobs_saved: totalJobsSaved,
      total_jobs_applied: totalJobsApplied,
      total_interviews: totalInterviews,
      total_offers: totalOffers,
      total_favorites: totalFavorites,
      success_rate: successRate,
    });
  } catch (error) {
    console.error("Unexpected error fetching stats:", error);
    const message = error instanceof Error ? error.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
