"use client";

import Link from "next/link";
import { Plus } from "lucide-react";
import { useMemo } from "react";

import { Button } from "@/components/ui/button";
import { ActivityHeatMap } from "@/components/dashboard/ActivityHeatMap";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useUserStats } from "@/lib/hooks/useUserStats";
import { useJobs } from "@/lib/hooks/useJobs";

export default function Home() {
  const { data: user, isLoading: isLoadingUser } = useCurrentUser();
  const { data: stats, isLoading: isLoadingStats } = useUserStats(user?.id);

  // Fetch all jobs for the heat map and calculating days since last application
  const { data: jobsData } = useJobs({
    userId: user?.id ?? 0,
    limit: 1000, // Large limit to get all jobs
  });
  const jobs = jobsData?.items ?? [];

  // Calculate days since last application
  const daysSinceLastApplication = useMemo(() => {
    const appliedJobs = jobs.filter((job) => job.applied_at);
    if (appliedJobs.length === 0) {
      return "N/A";
    }

    // Find the most recent applied_at date
    const dates = appliedJobs
      .map((job) => job.applied_at!)
      .map((dateStr) => new Date(dateStr))
      .sort((a, b) => b.getTime() - a.getTime());

    const mostRecentDate = dates[0];
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    mostRecentDate.setHours(0, 0, 0, 0);

    const diffTime = today.getTime() - mostRecentDate.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return "Today";
    } else if (diffDays === 1) {
      return "1 day";
    } else {
      return `${diffDays} days`;
    }
  }, [jobs]);

  if (isLoadingUser) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-destructive">
          Unable to load user. Please refresh the page.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with Add Job Button */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your job application activity
          </p>
        </div>
        <Button asChild size="lg">
          <Link href="/intake/new/details">
            <Plus className="mr-2 size-4" />
            Add Job
          </Link>
        </Button>
      </div>

      {/* Primary Stats Row */}
      {isLoadingStats ? (
        <div className="text-muted-foreground">Loading statistics...</div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            <div className="flex flex-col items-center text-center">
              <p className="text-3xl font-bold">
                {stats?.jobs_applied_7_days ?? 0}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Jobs Applied (Last 7 Days)
              </p>
            </div>
            <div className="flex flex-col items-center text-center">
              <p className="text-3xl font-bold">
                {stats?.jobs_applied_30_days ?? 0}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                Jobs Applied (Last 30 Days)
              </p>
            </div>
            <div className="flex flex-col items-center text-center">
              <p className="text-3xl font-bold">{daysSinceLastApplication}</p>
              <p className="text-sm text-muted-foreground mt-1">
                Days Since Last Application
              </p>
            </div>
          </div>

          {/* Secondary Stats Row */}
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <div className="text-center">
              <p className="text-base font-medium">
                {stats?.total_jobs_applied ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">
                Total Jobs Applied
              </p>
            </div>
            <div className="text-center">
              <p className="text-base font-medium">
                {stats?.total_jobs_saved ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">Total Jobs Saved</p>
            </div>
            <div className="text-center">
              <p className="text-base font-medium">
                {stats?.total_interviews ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">
                Interviews Scheduled
              </p>
            </div>
            <div className="text-center">
              <p className="text-base font-medium">
                {stats?.total_offers ?? 0}
              </p>
              <p className="text-sm text-muted-foreground">Offers Received</p>
            </div>
          </div>
        </>
      )}

      {/* Activity Heat Map */}
      {user && <ActivityHeatMap jobs={jobs} />}
    </div>
  );
}
