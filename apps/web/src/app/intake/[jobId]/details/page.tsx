"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { JobDetailsForm, JobDetailsFormData } from "@/components/intake/JobDetailsForm";
import { useJob } from "@/lib/hooks/useJobs";
import { useIntakeStore } from "@/lib/store/intake";
import { jobsAPI } from "@/lib/api/jobs";
import { useQuery } from "@tanstack/react-query";

export default function IntakeDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = parseInt(params.jobId as string, 10);
  const [initialData, setInitialData] = useState<JobDetailsFormData | undefined>();

  const { setJobId, setSessionId } = useIntakeStore();

  // Fetch job data
  const { data: job, isLoading: isLoadingJob } = useJob(jobId);

  // Fetch or create intake session
  const { data: intakeSession } = useQuery({
    queryKey: ["intake-session", jobId],
    queryFn: () => jobsAPI.getIntakeSession(jobId),
    enabled: !!jobId,
    retry: false,
  });

  // Create intake session if it doesn't exist
  const createSession = async () => {
    try {
      const session = await jobsAPI.createIntakeSession(jobId);
      setSessionId(session.id.toString());
      return session;
    } catch (error) {
      console.error("Failed to create intake session:", error);
      throw error;
    }
  };

  // Initialize session ID
  useEffect(() => {
    if (intakeSession) {
      setSessionId(intakeSession.id.toString());
    }
  }, [intakeSession, setSessionId]);

  // Initialize form data when job is loaded
  useEffect(() => {
    if (job) {
      setInitialData({
        title: job.job_title || "",
        company: job.company_name || "",
        description: job.job_description || "",
        favorite: job.is_favorite || false,
      });
      setJobId(job.id);
    }
  }, [job, setJobId]);

  const handleComplete = async () => {
    if (!job) return;

    try {
      // Ensure intake session exists
      let session = intakeSession;
      if (!session) {
        session = await createSession();
      }

      // Update session to mark step 1 as completed
      if (session) {
        await jobsAPI.updateIntakeSession(job.id, {
          current_step: 2,
          step_completed: 1,
        });
      }

      // Navigate to experience step
      router.push(`/intake/${job.id}/experience`);
    } catch (error) {
      console.error("Failed to update intake session:", error);
    }
  };

  if (isLoadingJob) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!job) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <div className="text-destructive">Job not found</div>
        <Button onClick={() => router.push("/jobs")} variant="outline">
          Back to Jobs
        </Button>
      </div>
    );
  }

  return (
    <JobDetailsForm
      mode="edit"
      jobId={jobId}
      initialData={initialData}
      onComplete={handleComplete}
      onCancel={() => router.push(`/jobs/${jobId}`)}
    />
  );
}
