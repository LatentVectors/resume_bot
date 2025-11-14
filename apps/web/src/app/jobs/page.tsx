"use client";

import { useState } from "react";
import Link from "next/link";
import { Plus } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { JobCard } from "@/components/jobs/JobCard";
import { useJobs } from "@/lib/hooks/useJobs";
import { useCurrentUser } from "@/lib/hooks/useUser";
import type { components } from "@/types/api";

type JobStatus = components["schemas"]["JobStatus"];

const STATUS_OPTIONS: { value: JobStatus | "all"; label: string }[] = [
  { value: "all", label: "All Statuses" },
  { value: "Saved", label: "Saved" },
  { value: "Applied", label: "Applied" },
  { value: "Interviewing", label: "Interviewing" },
  { value: "Not Selected", label: "Not Selected" },
  { value: "No Offer", label: "No Offer" },
  { value: "Hired", label: "Hired" },
];

export default function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<JobStatus | "all">("all");
  const [favoriteOnly, setFavoriteOnly] = useState(false);

  // Fetch current user
  const { data: user, isLoading: isLoadingUser } = useCurrentUser();

  // Fetch jobs with filters
  const { data: jobs, isLoading: isLoadingJobs } = useJobs({
    userId: user?.id ?? 0,
    statusFilter: statusFilter === "all" ? null : statusFilter,
    favoriteOnly: favoriteOnly || undefined,
  });

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
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Jobs</h1>
          <p className="text-muted-foreground">
            Manage your job applications and track your progress
          </p>
        </div>
        <Button asChild>
          <Link href="/">
            <Plus className="mr-2 size-4" />
            Add Job
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filters</CardTitle>
          <CardDescription>Filter jobs by status or favorites</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="status-filter" className="text-sm font-medium">
                Status:
              </label>
              <Select
                value={statusFilter}
                onValueChange={(value) =>
                  setStatusFilter(value as JobStatus | "all")
                }
              >
                <SelectTrigger id="status-filter" className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="flex items-center gap-2">
              <label htmlFor="favorite-filter" className="text-sm font-medium">
                Favorites:
              </label>
              <Button
                id="favorite-filter"
                variant={favoriteOnly ? "default" : "outline"}
                size="sm"
                onClick={() => setFavoriteOnly(!favoriteOnly)}
              >
                {favoriteOnly ? "Show All" : "Favorites Only"}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Jobs List */}
      {isLoadingJobs ? (
        <div className="flex min-h-[400px] items-center justify-center">
          <div className="text-muted-foreground">Loading jobs...</div>
        </div>
      ) : !jobs || jobs.length === 0 ? (
        <Card>
          <CardContent className="flex min-h-[400px] flex-col items-center justify-center">
            <p className="mb-4 text-lg text-muted-foreground">
              {favoriteOnly
                ? "No favorite jobs found"
                : statusFilter !== "all"
                  ? `No jobs with status "${statusFilter}"`
                  : "No jobs yet"}
            </p>
            <Button asChild>
              <Link href="/">
                <Plus className="mr-2 size-4" />
                Add Your First Job
              </Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}

      {/* Results count */}
      {jobs && jobs.length > 0 && (
        <div className="text-center text-sm text-muted-foreground">
          Showing {jobs.length} job{jobs.length !== 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}

