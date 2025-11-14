"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Star, Trash2, Edit2, Save, X } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  useDeleteJob,
  useToggleFavorite,
  useUpdateJob,
  useUpdateJobStatus,
} from "@/lib/hooks/useJobMutations";
import type { components } from "@/types/api";

type JobResponse = components["schemas"]["JobResponse"];
type JobStatus = components["schemas"]["JobStatus"];

const STATUS_OPTIONS: JobStatus[] = [
  "Saved",
  "Applied",
  "Interviewing",
  "Not Selected",
  "No Offer",
  "Hired",
];

interface OverviewTabProps {
  job: JobResponse;
}

export function OverviewTab({ job }: OverviewTabProps) {
  const router = useRouter();
  const [isEditing, setIsEditing] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [formData, setFormData] = useState({
    job_title: job.job_title || "",
    company_name: job.company_name || "",
    job_description: job.job_description || "",
    status: job.status,
  });

  const updateJob = useUpdateJob();
  const deleteJob = useDeleteJob();
  const toggleFavorite = useToggleFavorite();
  const updateStatus = useUpdateJobStatus();

  const handleSave = async () => {
    try {
      await updateJob.mutateAsync({
        jobId: job.id,
        data: {
          job_title: formData.job_title || null,
          company_name: formData.company_name || null,
          job_description: formData.job_description || null,
        },
      });
      setIsEditing(false);
    } catch (error) {
      console.error("Failed to update job:", error);
    }
  };

  const handleCancel = () => {
    setFormData({
      job_title: job.job_title || "",
      company_name: job.company_name || "",
      job_description: job.job_description || "",
      status: job.status,
    });
    setIsEditing(false);
  };

  const handleDelete = async () => {
    try {
      await deleteJob.mutateAsync(job.id);
      setShowDeleteDialog(false);
      router.push("/jobs");
    } catch (error) {
      console.error("Failed to delete job:", error);
    }
  };

  const handleToggleFavorite = async () => {
    try {
      await toggleFavorite.mutateAsync({
        jobId: job.id,
        favorite: !job.is_favorite,
      });
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    }
  };

  const handleStatusChange = async (newStatus: JobStatus) => {
    try {
      await updateStatus.mutateAsync({
        jobId: job.id,
        status: newStatus,
      });
      setFormData((prev) => ({ ...prev, status: newStatus }));
    } catch (error) {
      console.error("Failed to update status:", error);
    }
  };

  return (
    <>
      <div className="space-y-6">
        {/* Header Actions */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold">
              {job.job_title || "Untitled Position"}
            </h2>
            {job.is_favorite && (
              <Star className="size-5 fill-yellow-400 text-yellow-400" />
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleToggleFavorite}
              disabled={toggleFavorite.isPending}
            >
              <Star
                className={`size-4 ${job.is_favorite ? "fill-yellow-400 text-yellow-400" : ""}`}
              />
            </Button>
            {!isEditing ? (
              <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                <Edit2 className="mr-2 size-4" />
                Edit
              </Button>
            ) : (
              <>
                <Button variant="outline" size="sm" onClick={handleCancel}>
                  <X className="mr-2 size-4" />
                  Cancel
                </Button>
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={updateJob.isPending}
                >
                  <Save className="mr-2 size-4" />
                  {updateJob.isPending ? "Saving..." : "Save"}
                </Button>
              </>
            )}
            <Button
              variant="destructive"
              size="sm"
              onClick={() => setShowDeleteDialog(true)}
            >
              <Trash2 className="mr-2 size-4" />
              Delete
            </Button>
          </div>
        </div>

        {/* Job Details Card */}
        <Card>
          <CardHeader>
            <CardTitle>Job Details</CardTitle>
            <CardDescription>Basic information about this job</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Status */}
            <div className="flex items-center gap-4">
              <Label htmlFor="status" className="w-24">
                Status:
              </Label>
              {isEditing ? (
                <Select
                  value={formData.status}
                  onValueChange={(value) => handleStatusChange(value as JobStatus)}
                >
                  <SelectTrigger id="status" className="w-[200px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {STATUS_OPTIONS.map((status) => (
                      <SelectItem key={status} value={status}>
                        {status}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : (
                <Badge variant="secondary">{job.status}</Badge>
              )}
            </div>

            {/* Job Title */}
            <div className="flex items-start gap-4">
              <Label htmlFor="job_title" className="w-24 pt-2">
                Title:
              </Label>
              {isEditing ? (
                <Input
                  id="job_title"
                  value={formData.job_title}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, job_title: e.target.value }))
                  }
                  placeholder="Job title"
                  className="flex-1"
                />
              ) : (
                <div className="flex-1 pt-2">
                  {job.job_title || (
                    <span className="text-muted-foreground">No title</span>
                  )}
                </div>
              )}
            </div>

            {/* Company Name */}
            <div className="flex items-start gap-4">
              <Label htmlFor="company_name" className="w-24 pt-2">
                Company:
              </Label>
              {isEditing ? (
                <Input
                  id="company_name"
                  value={formData.company_name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, company_name: e.target.value }))
                  }
                  placeholder="Company name"
                  className="flex-1"
                />
              ) : (
                <div className="flex-1 pt-2">
                  {job.company_name || (
                    <span className="text-muted-foreground">No company name</span>
                  )}
                </div>
              )}
            </div>

            {/* Job Description */}
            <div className="flex items-start gap-4">
              <Label htmlFor="job_description" className="w-24 pt-2">
                Description:
              </Label>
              {isEditing ? (
                <Textarea
                  id="job_description"
                  value={formData.job_description}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, job_description: e.target.value }))
                  }
                  placeholder="Job description"
                  className="flex-1 min-h-[200px]"
                />
              ) : (
                <div className="flex-1 pt-2">
                  {job.job_description ? (
                    <p className="whitespace-pre-wrap">{job.job_description}</p>
                  ) : (
                    <span className="text-muted-foreground">No description</span>
                  )}
                </div>
              )}
            </div>

            {/* Metadata */}
            <div className="flex items-center gap-6 pt-4 text-sm text-muted-foreground">
              <div>
                Created: {new Date(job.created_at).toLocaleDateString()}
              </div>
              {job.applied_at && (
                <div>
                  Applied: {new Date(job.applied_at).toLocaleDateString()}
                </div>
              )}
              {job.updated_at && (
                <div>
                  Updated: {new Date(job.updated_at).toLocaleDateString()}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Job</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this job? This action cannot be undone.
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

