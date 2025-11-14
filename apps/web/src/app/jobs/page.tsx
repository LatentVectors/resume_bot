"use client";

import { useState, useMemo, Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Plus,
  Star,
  Trash2,
  MoreVertical,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
  Briefcase,
  FileText,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useJobs } from "@/lib/hooks/useJobs";
import { useCurrentUser } from "@/lib/hooks/useUser";
import {
  useBulkDeleteJobs,
  useToggleFavorite,
} from "@/lib/hooks/useJobMutations";
import type { components } from "@/types/api";

type JobStatus = components["schemas"]["JobStatus"];

const STATUS_OPTIONS: { value: JobStatus; label: string }[] = [
  { value: "Saved", label: "Saved" },
  { value: "Applied", label: "Applied" },
  { value: "Interviewing", label: "Interviewing" },
  { value: "Not Selected", label: "Not Selected" },
  { value: "No Offer", label: "No Offer" },
  { value: "Hired", label: "Hired" },
];

const statusColors: Record<
  JobStatus,
  "default" | "secondary" | "outline" | "destructive"
> = {
  Saved: "secondary",
  Applied: "default",
  Interviewing: "default",
  "Not Selected": "destructive",
  "No Offer": "destructive",
  Hired: "default",
};

const JOBS_PER_PAGE = 50;

type SortField = "created_at" | "job_title" | "company_name" | "status";
type SortDirection = "asc" | "desc";

function JobsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();

  // Get pagination from URL
  const page = parseInt(searchParams.get("page") || "1", 10);
  const skip = (page - 1) * JOBS_PER_PAGE;

  // Filters
  const [statusFilters, setStatusFilters] = useState<Set<JobStatus>>(new Set());
  const [favoriteOnly, setFavoriteOnly] = useState(false);
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  // Selection
  const [selectedJobIds, setSelectedJobIds] = useState<Set<number>>(new Set());
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Fetch current user
  const { data: user, isLoading: isLoadingUser } = useCurrentUser();

  // Determine status filter for API (single status if only one selected, null if none or all)
  // Note: When multiple statuses are selected, we fetch all and filter client-side
  const statusFilter: JobStatus | null = useMemo(() => {
    if (
      statusFilters.size === 0 ||
      statusFilters.size === STATUS_OPTIONS.length
    ) {
      return null;
    }
    if (statusFilters.size === 1) {
      return Array.from(statusFilters)[0];
    }
    // Multiple selected - fetch all and filter client-side
    return null;
  }, [statusFilters]);

  // Fetch jobs with filters
  // When multiple statuses selected, we need to fetch all jobs (no skip/limit) and paginate client-side
  const needsClientSideFiltering = statusFilters.size > 1;
  const { data: jobsData, isLoading: isLoadingJobs } = useJobs({
    userId: user?.id ?? 0,
    statusFilter: statusFilter,
    favoriteOnly: favoriteOnly || undefined,
    skip: needsClientSideFiltering ? undefined : skip,
    limit: needsClientSideFiltering ? undefined : JOBS_PER_PAGE,
  });

  const bulkDeleteJobs = useBulkDeleteJobs();
  const toggleFavorite = useToggleFavorite();

  // Client-side filtering for multiple statuses and sorting
  const { filteredJobs, totalFilteredJobs } = useMemo(() => {
    if (!jobsData || !jobsData.items || !Array.isArray(jobsData.items))
      return { filteredJobs: [], totalFilteredJobs: 0 };
    let jobs = [...jobsData.items];

    // Apply multi-status filter if multiple statuses selected
    if (statusFilters.size > 0 && statusFilters.size < STATUS_OPTIONS.length) {
      jobs = jobs.filter((job) => statusFilters.has(job.status));
    }

    // Apply favorite filter
    if (favoriteOnly) {
      jobs = jobs.filter((job) => job.is_favorite);
    }

    const totalFiltered = jobs.length;

    // Apply sorting
    jobs.sort((a, b) => {
      let aVal: string | number | Date;
      let bVal: string | number | Date;

      switch (sortField) {
        case "created_at":
          aVal = new Date(a.created_at).getTime();
          bVal = new Date(b.created_at).getTime();
          break;
        case "job_title":
          aVal = (a.job_title || "").toLowerCase();
          bVal = (b.job_title || "").toLowerCase();
          break;
        case "company_name":
          aVal = (a.company_name || "").toLowerCase();
          bVal = (b.company_name || "").toLowerCase();
          break;
        case "status":
          aVal = a.status;
          bVal = b.status;
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortDirection === "asc" ? -1 : 1;
      if (aVal > bVal) return sortDirection === "asc" ? 1 : -1;
      return 0;
    });

    // Apply client-side pagination if needed
    if (needsClientSideFiltering) {
      const startIndex = skip;
      const endIndex = startIndex + JOBS_PER_PAGE;
      jobs = jobs.slice(startIndex, endIndex);
    }

    return { filteredJobs: jobs, totalFilteredJobs: totalFiltered };
  }, [
    jobsData,
    statusFilters,
    favoriteOnly,
    sortField,
    sortDirection,
    skip,
    needsClientSideFiltering,
  ]);

  const totalJobs = needsClientSideFiltering
    ? totalFilteredJobs
    : jobsData?.total ?? 0;
  const totalPages = Math.ceil(totalJobs / JOBS_PER_PAGE);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedJobIds(new Set(filteredJobs.map((job) => job.id)));
    } else {
      setSelectedJobIds(new Set());
    }
  };

  const handleSelectJob = (jobId: number, checked: boolean) => {
    const newSelection = new Set(selectedJobIds);
    if (checked) {
      newSelection.add(jobId);
    } else {
      newSelection.delete(jobId);
    }
    setSelectedJobIds(newSelection);
  };

  const handleBulkDelete = async () => {
    if (selectedJobIds.size === 0) return;
    try {
      await bulkDeleteJobs.mutateAsync(Array.from(selectedJobIds));
      setSelectedJobIds(new Set());
      setShowDeleteDialog(false);
    } catch (error) {
      console.error("Failed to delete jobs:", error);
    }
  };

  const handleToggleFavorite = async (
    e: React.MouseEvent,
    jobId: number,
    currentFavorite: boolean
  ) => {
    e.stopPropagation();
    try {
      await toggleFavorite.mutateAsync({ jobId, favorite: !currentFavorite });
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    }
  };

  const handleRowClick = (jobId: number) => {
    router.push(`/jobs/${jobId}`);
  };

  const handleStatusFilterToggle = (status: JobStatus, checked: boolean) => {
    const newFilters = new Set(statusFilters);
    if (checked) {
      newFilters.add(status);
    } else {
      newFilters.delete(status);
    }
    setStatusFilters(newFilters);
  };

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.set("page", newPage.toString());
    router.push(`/jobs?${params.toString()}`);
    setSelectedJobIds(new Set()); // Clear selection on page change
  };

  const allSelected =
    filteredJobs.length > 0 && selectedJobIds.size === filteredJobs.length;

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
    <div className="mx-auto max-w-7xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Jobs</h1>
          <p className="text-muted-foreground">
            Manage your job applications and track your progress
          </p>
        </div>
        <Button asChild>
          <Link href="/intake/new/details">
            <Plus className="mr-2 size-4" />
            Add Job
          </Link>
        </Button>
      </div>

      {/* Compact Filters */}
      <div className="flex h-[50px] items-center gap-4 border-b pb-4">
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" size="sm" className="h-8">
              Status
              {statusFilters.size > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {statusFilters.size}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-56" align="start">
            <div className="space-y-2">
              {STATUS_OPTIONS.map((option) => (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`status-${option.value}`}
                    checked={statusFilters.has(option.value)}
                    onCheckedChange={(checked) =>
                      handleStatusFilterToggle(option.value, checked === true)
                    }
                  />
                  <label
                    htmlFor={`status-${option.value}`}
                    className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
                  >
                    {option.label}
                  </label>
                </div>
              ))}
            </div>
          </PopoverContent>
        </Popover>

        <div className="flex items-center space-x-2">
          <Checkbox
            id="favorites-only"
            checked={favoriteOnly}
            onCheckedChange={(checked) => setFavoriteOnly(checked === true)}
          />
          <label
            htmlFor="favorites-only"
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 cursor-pointer"
          >
            Show favorites only
          </label>
        </div>
      </div>

      {/* Bulk Actions Toolbar */}
      {selectedJobIds.size > 0 && (
        <div className="flex items-center justify-between rounded-md border bg-muted/50 px-4 py-2">
          <span className="text-sm font-medium">
            {selectedJobIds.size} job{selectedJobIds.size !== 1 ? "s" : ""}{" "}
            selected
          </span>
          <Button
            variant="destructive"
            size="sm"
            onClick={() => setShowDeleteDialog(true)}
          >
            <Trash2 className="mr-2 size-4" />
            Delete Selected
          </Button>
        </div>
      )}

      {/* Jobs Table */}
      {isLoadingJobs ? (
        <div className="flex min-h-[400px] items-center justify-center">
          <div className="text-muted-foreground">Loading jobs...</div>
        </div>
      ) : !filteredJobs || filteredJobs.length === 0 ? (
        <div className="flex min-h-[400px] flex-col items-center justify-center rounded-md border">
          <p className="mb-4 text-lg text-muted-foreground">
            {favoriteOnly
              ? "No favorite jobs found"
              : statusFilters.size > 0
              ? "No jobs match the selected filters"
              : "No jobs yet"}
          </p>
          <Button asChild>
            <Link href="/intake/new/details">
              <Plus className="mr-2 size-4" />
              Add Your First Job
            </Link>
          </Button>
        </div>
      ) : (
        <>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-12">
                    <Checkbox
                      checked={allSelected}
                      onCheckedChange={handleSelectAll}
                      aria-label="Select all"
                    />
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 -ml-3"
                      onClick={() => handleSort("job_title")}
                    >
                      Job Title
                      <ArrowUpDown className="ml-2 size-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 -ml-3"
                      onClick={() => handleSort("company_name")}
                    >
                      Company
                      <ArrowUpDown className="ml-2 size-4" />
                    </Button>
                  </TableHead>
                  <TableHead className="w-16">Favorite</TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 -ml-3"
                      onClick={() => handleSort("status")}
                    >
                      Status
                      <ArrowUpDown className="ml-2 size-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 -ml-3"
                      onClick={() => handleSort("created_at")}
                    >
                      Date Added
                      <ArrowUpDown className="ml-2 size-4" />
                    </Button>
                  </TableHead>
                  <TableHead className="w-32">Documents</TableHead>
                  <TableHead className="w-16">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredJobs.map((job) => (
                  <TableRow
                    key={job.id}
                    className="cursor-pointer"
                    onClick={() => handleRowClick(job.id)}
                  >
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Checkbox
                        checked={selectedJobIds.has(job.id)}
                        onCheckedChange={(checked) =>
                          handleSelectJob(job.id, checked === true)
                        }
                        onClick={(e) => e.stopPropagation()}
                      />
                    </TableCell>
                    <TableCell className="font-medium">
                      {job.job_title || "Untitled Position"}
                    </TableCell>
                    <TableCell>{job.company_name || "—"}</TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        onClick={(e) =>
                          handleToggleFavorite(e, job.id, job.is_favorite)
                        }
                      >
                        <Star
                          className={`size-4 ${
                            job.is_favorite
                              ? "fill-yellow-400 text-yellow-400"
                              : "text-muted-foreground"
                          }`}
                        />
                      </Button>
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusColors[job.status]}>
                        {job.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(job.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {job.has_resume && (
                          <Badge variant="outline" className="gap-1">
                            <Briefcase className="size-3" />
                            Resume
                          </Badge>
                        )}
                        {job.has_cover_letter && (
                          <Badge variant="outline" className="gap-1">
                            <FileText className="size-3" />
                            Cover Letter
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell onClick={(e) => e.stopPropagation()}>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 w-8 p-0"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreVertical className="size-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem
                            onClick={() => handleRowClick(job.id)}
                          >
                            View Details
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Showing {skip + 1} to{" "}
                {Math.min(skip + JOBS_PER_PAGE, totalJobs)} of {totalJobs} jobs
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page - 1)}
                  disabled={page === 1}
                >
                  <ChevronLeft className="size-4" />
                  Previous
                </Button>
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum: number;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (page <= 3) {
                      pageNum = i + 1;
                    } else if (page >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = page - 2 + i;
                    }
                    return (
                      <Button
                        key={pageNum}
                        variant={page === pageNum ? "default" : "outline"}
                        size="sm"
                        onClick={() => handlePageChange(pageNum)}
                        className="w-10"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(page + 1)}
                  disabled={page >= totalPages}
                >
                  Next
                  <ChevronRight className="size-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Bulk Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Selected Jobs</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete {selectedJobIds.size} job
              {selectedJobIds.size !== 1 ? "s" : ""}? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={bulkDeleteJobs.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleBulkDelete}
              disabled={bulkDeleteJobs.isPending}
            >
              {bulkDeleteJobs.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default function JobsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-[60vh] items-center justify-center">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      }
    >
      <JobsPageContent />
    </Suspense>
  );
}
