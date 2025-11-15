"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Star, Trash2, Edit2, Save, X, MoreVertical, Download, Copy } from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { useCurrentResume, useResumeVersions } from "@/lib/hooks/useResumes";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useExperiences } from "@/lib/hooks/useExperiences";
import { resumesAPI } from "@/lib/api/resumes";
import { jobsAPI } from "@/lib/api/jobs";
import { experiencesAPI } from "@/lib/api/experiences";
import { formatAllExperiences } from "@/lib/utils/formatExperiences";
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
  const [hasCanonicalResume, setHasCanonicalResume] = useState(false);
  const [isDownloadingResume, setIsDownloadingResume] = useState(false);
  const [isCopyingContext, setIsCopyingContext] = useState(false);

  const { data: user } = useCurrentUser();
  const { data: currentResume } = useCurrentResume(job.id);
  const { data: versions } = useResumeVersions(job.id);
  const { data: experiences } = useExperiences(user?.id ?? 0);

  const updateJob = useUpdateJob();
  const deleteJob = useDeleteJob();
  const toggleFavorite = useToggleFavorite();
  const updateStatus = useUpdateJobStatus();

  // Check if canonical resume exists and find matching version
  useEffect(() => {
    if (currentResume && versions) {
      setHasCanonicalResume(true);
    } else {
      setHasCanonicalResume(false);
    }
  }, [currentResume, versions]);

  const handleSave = async () => {
    try {
      await updateJob.mutateAsync({
        jobId: job.id,
        data: {
          title: formData.job_title || null,
          company: formData.company_name || null,
          description: formData.job_description || "",
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

  const handleDownloadResume = async () => {
    if (!currentResume) {
      toast.error("No resume available to download");
      return;
    }

    // Find the matching version by comparing resume_json and template_name
    let matchingVersionId: number | null = null;
    if (versions) {
      const matchingVersion = versions.find(
        (v) =>
          v.resume_json === currentResume.resume_json &&
          v.template_name === currentResume.template_name
      );
      matchingVersionId = matchingVersion?.id ?? null;
    }

    if (!matchingVersionId) {
      toast.error("Unable to find resume version to download");
      return;
    }

    setIsDownloadingResume(true);
    try {
      const blob = await resumesAPI.downloadPDF(job.id, matchingVersionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      
      // Build filename similar to Streamlit app
      const companyName = job.company_name || "company";
      const jobTitle = job.job_title || "position";
      
      // Parse resume_json to get name
      let fullName = "resume";
      try {
        const resumeData = JSON.parse(currentResume.resume_json);
        fullName = resumeData.name || "resume";
      } catch {
        // Use default if parsing fails
      }
      
      const filename = `${companyName}_${jobTitle}_${fullName}_resume.pdf`
        .replace(/[^a-zA-Z0-9_-]/g, "_")
        .toLowerCase();
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      toast.success("Resume downloaded successfully");
    } catch (error) {
      console.error("Failed to download resume:", error);
      toast.error("Failed to download resume. Please try again.");
    } finally {
      setIsDownloadingResume(false);
    }
  };

  const handleCopyJobContext = async () => {
    if (!user?.id) {
      toast.error("User information not available");
      return;
    }

    setIsCopyingContext(true);
    try {
      // Fetch all required data
      const [intakeSession, userExperiences] = await Promise.all([
        jobsAPI.getIntakeSession(job.id).catch(() => null),
        experiencesAPI.list(user.id),
      ]);

      // Fetch achievements for each experience
      const achievementsByExp = new Map<number, components["schemas"]["AchievementResponse"][]>();
      if (userExperiences) {
        await Promise.all(
          userExperiences.map(async (exp) => {
            try {
              const achievements = await experiencesAPI.listAchievements(exp.id);
              achievementsByExp.set(exp.id, achievements);
            } catch (error) {
              console.error(`Failed to fetch achievements for experience ${exp.id}:`, error);
            }
          })
        );
      }

      // Format work experience
      const workExperience = userExperiences
        ? formatAllExperiences(userExperiences, achievementsByExp)
        : "No work experience available.";

      // Get job description
      const jobDescription = job.job_description || "";

      // Get analyses from intake session
      const gapAnalysis = intakeSession?.gap_analysis || "";
      const stakeholderAnalysis = intakeSession?.stakeholder_analysis || "";

      // Build the formatted prompt (XML-style tags as in Streamlit app)
      const prompt = `<work_experience>
${workExperience}
</work_experience>

<job_description>
${jobDescription}
</job_description>

<gap_analysis>
${gapAnalysis}
</gap_analysis>

<stakeholder_analysis>
${stakeholderAnalysis}
</stakeholder_analysis>
`;

      // Copy to clipboard
      await navigator.clipboard.writeText(prompt);
      toast.success("Job context copied to clipboard!");
    } catch (error) {
      console.error("Failed to copy job context:", error);
      toast.error("Failed to copy job context. Please try again.");
    } finally {
      setIsCopyingContext(false);
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
              variant="ghost"
              size="sm"
              onClick={handleToggleFavorite}
              disabled={toggleFavorite.isPending}
            >
              <Star
                className={`size-4 ${job.is_favorite ? "fill-yellow-400 text-yellow-400" : ""}`}
              />
            </Button>
            {!isEditing ? (
              <>
                <Button variant="outline" size="sm" onClick={() => setIsEditing(true)}>
                  Edit
                </Button>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setShowDeleteDialog(true)}
                >
                  Delete
                </Button>
              </>
            ) : (
              <>
                <Button variant="outline" size="sm" onClick={handleCancel}>
                  Discard
                </Button>
                <Button
                  size="sm"
                  onClick={handleSave}
                  disabled={updateJob.isPending}
                >
                  {updateJob.isPending ? "Saving..." : "Save"}
                </Button>
              </>
            )}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <MoreVertical className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem
                  onClick={handleDownloadResume}
                  disabled={!hasCanonicalResume || isDownloadingResume}
                >
                  <Download className="mr-2 size-4" />
                  Download Resume
                </DropdownMenuItem>
                <DropdownMenuItem disabled>
                  <Download className="mr-2 size-4" />
                  Download Cover Letter
                </DropdownMenuItem>
                <DropdownMenuItem disabled>
                  <Copy className="mr-2 size-4" />
                  Copy Cover Letter
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleCopyJobContext}
                  disabled={isCopyingContext}
                >
                  <Copy className="mr-2 size-4" />
                  Copy Job Context
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>

        {/* Job Details */}
        <div className="space-y-6">
          {/* Row 1: Title and Company (4 columns, using first 2) */}
          <div className="grid grid-cols-4 gap-6">
            {/* Job Title */}
            <div className="space-y-2">
              <Label htmlFor="job_title" className="text-sm font-medium">
                Title
              </Label>
              {isEditing ? (
                <Input
                  id="job_title"
                  value={formData.job_title}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, job_title: e.target.value }))
                  }
                  placeholder="Job title"
                />
              ) : (
                <div className="text-sm">
                  {job.job_title || (
                    <span className="text-muted-foreground">No title</span>
                  )}
                </div>
              )}
            </div>

            {/* Company Name */}
            <div className="space-y-2">
              <Label htmlFor="company_name" className="text-sm font-medium">
                Company
              </Label>
              {isEditing ? (
                <Input
                  id="company_name"
                  value={formData.company_name}
                  onChange={(e) =>
                    setFormData((prev) => ({ ...prev, company_name: e.target.value }))
                  }
                  placeholder="Company name"
                />
              ) : (
                <div className="text-sm">
                  {job.company_name || (
                    <span className="text-muted-foreground">No company name</span>
                  )}
                </div>
              )}
            </div>
          </div>

          {/* Row 2: Status, Date Created, Date Updated (4 columns, using first 3) */}
          <div className="grid grid-cols-4 gap-6">
            {/* Status */}
            <div className="space-y-2">
              <Label htmlFor="status" className="text-sm font-medium">
                Status
              </Label>
              {isEditing ? (
                <Select
                  value={formData.status}
                  onValueChange={(value) => handleStatusChange(value as JobStatus)}
                >
                  <SelectTrigger id="status">
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
                <div>
                  <Badge variant="secondary">{job.status}</Badge>
                </div>
              )}
            </div>

            {/* Date Created */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Date Created</Label>
              <div className="text-sm text-muted-foreground">
                {new Date(job.created_at).toLocaleDateString()}
              </div>
            </div>

            {/* Date Updated */}
            <div className="space-y-2">
              <Label className="text-sm font-medium">Date Updated</Label>
              <div className="text-sm text-muted-foreground">
                {job.updated_at ? new Date(job.updated_at).toLocaleDateString() : '—'}
              </div>
            </div>
          </div>

          {/* Row 3: Description */}
          <div className="space-y-2">
            <Label htmlFor="job_description" className="text-sm font-medium">
              Description
            </Label>
            {isEditing ? (
              <Textarea
                id="job_description"
                value={formData.job_description}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, job_description: e.target.value }))
                }
                placeholder="Job description"
                className="min-h-[200px]"
              />
            ) : (
              <div className="text-sm">
                {job.job_description ? (
                  <p className="whitespace-pre-wrap">{job.job_description}</p>
                ) : (
                  <span className="text-muted-foreground">No description</span>
                )}
              </div>
            )}
          </div>
        </div>
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

