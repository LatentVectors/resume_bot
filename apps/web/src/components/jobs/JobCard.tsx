"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Trash2, Star, Building2, Briefcase } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useDeleteJob } from "@/lib/hooks/useJobMutations";
import type { components } from "@/types/api";

type JobResponse = components["schemas"]["JobResponse"];

interface JobCardProps {
  job: JobResponse;
  onDelete?: () => void;
}

const statusColors: Record<
  components["schemas"]["JobStatus"],
  "default" | "secondary" | "outline" | "destructive"
> = {
  Saved: "secondary",
  Applied: "default",
  Interviewing: "default",
  "Not Selected": "destructive",
  "No Offer": "destructive",
  Hired: "default",
};

export function JobCard({ job, onDelete }: JobCardProps) {
  const router = useRouter();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const deleteJob = useDeleteJob();

  const handleDelete = async () => {
    try {
      await deleteJob.mutateAsync(job.id);
      setShowDeleteDialog(false);
      onDelete?.();
    } catch (error) {
      console.error("Failed to delete job:", error);
    }
  };

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't navigate if clicking on buttons or links
    const target = e.target as HTMLElement;
    if (
      target.closest("button") ||
      target.closest("a") ||
      target.closest("[role='button']")
    ) {
      return;
    }
    router.push(`/jobs/${job.id}`);
  };

  return (
    <>
      <Card
        className="cursor-pointer transition-shadow hover:shadow-md"
        onClick={handleCardClick}
      >
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1 space-y-1">
              <CardTitle className="flex items-center gap-2">
                {job.job_title || "Untitled Position"}
                {job.is_favorite && (
                  <Star className="size-4 fill-yellow-400 text-yellow-400" />
                )}
              </CardTitle>
              <CardDescription className="flex items-center gap-2">
                {job.company_name ? (
                  <>
                    <Building2 className="size-4" />
                    {job.company_name}
                  </>
                ) : (
                  <span className="text-muted-foreground">No company name</span>
                )}
              </CardDescription>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
              onClick={(e) => {
                e.stopPropagation();
                setShowDeleteDialog(true);
              }}
              disabled={deleteJob.isPending}
            >
              <Trash2 className="size-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={statusColors[job.status]}>
              {job.status}
            </Badge>
            {job.has_resume && (
              <Badge variant="outline" className="gap-1">
                <Briefcase className="size-3" />
                Resume
              </Badge>
            )}
            {job.has_cover_letter && (
              <Badge variant="outline" className="gap-1">
                Cover Letter
              </Badge>
            )}
          </div>
          {job.job_description && (
            <p className="mt-3 line-clamp-2 text-sm text-muted-foreground">
              {job.job_description}
            </p>
          )}
        </CardContent>
        <CardFooter className="flex justify-between text-xs text-muted-foreground">
          <span>
            Created {new Date(job.created_at).toLocaleDateString()}
          </span>
          {job.applied_at && (
            <span>
              Applied {new Date(job.applied_at).toLocaleDateString()}
            </span>
          )}
        </CardFooter>
      </Card>

      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Job</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this job? This action cannot be
              undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              disabled={deleteJob.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteJob.isPending}
            >
              {deleteJob.isPending ? "Deleting..." : "Delete"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

