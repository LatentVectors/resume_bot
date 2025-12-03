"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useRef } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { JobDetailsForm, JobDetailsFormData } from "@/components/intake/JobDetailsForm";
import { useJob } from "@/lib/hooks/useJobs";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useIntakeInitialization } from "@/lib/hooks/useIntakeInitialization";
import { useIntakeStore } from "@/lib/store/intake";
import { jobsAPI } from "@/lib/api/jobs";
import { useQuery } from "@tanstack/react-query";

export default function IntakeDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = parseInt(params.jobId as string, 10);
  const [initialData, setInitialData] = useState<JobDetailsFormData | undefined>();
  const [isProcessing, setIsProcessing] = useState(false);
  // Track original job description to detect changes
  const originalDescriptionRef = useRef<string>("");

  const { setJobId, setSessionId } = useIntakeStore();
  const { data: user } = useCurrentUser();
  const { 
    initializeIntake, 
    isInitializing, 
    statusMessage,
    error: initError,
  } = useIntakeInitialization();

  // Fetch job data
  const { data: job, isLoading: isLoadingJob } = useJob(jobId);

  // Fetch or create intake session
  const { data: intakeSession } = useQuery({
    queryKey: ["intake-session", jobId],
    queryFn: () => jobsAPI.getIntakeSession(jobId),
    enabled: !!jobId,
    retry: false,
  });

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
      // Store original description to detect changes
      originalDescriptionRef.current = job.job_description || "";
    }
  }, [job, setJobId]);

  const handleComplete = async () => {
    if (!job || !user) return;

    setIsProcessing(true);
    try {
      // Check if we need to regenerate analyses
      // Regenerate if: no analyses exist OR job description changed
      const currentDescription = job.job_description || "";
      const descriptionChanged = currentDescription !== originalDescriptionRef.current;
      const needsAnalyses = !intakeSession?.gap_analysis?.trim() || 
                           !intakeSession?.stakeholder_analysis?.trim();
      const forceRegenerate = descriptionChanged;

      if (needsAnalyses || forceRegenerate) {
        // Run intake initialization with analyses
        const result = await initializeIntake({
          jobId: job.id,
          userId: user.id,
          jobDescription: currentDescription,
          forceRegenerate,
        });
        setSessionId(result.sessionId.toString());
      } else {
        // Analyses exist and description hasn't changed, just update step
        await jobsAPI.updateIntakeSession(job.id, {
          current_step: 2,
          step_completed: 1,
        });
      }

      // Navigate to experience step
      router.push(`/intake/${job.id}/experience`);
    } catch (error) {
      console.error("Failed to process intake session:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Show loading while processing or initializing analyses
  if (isProcessing || isInitializing) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
        <div className="text-muted-foreground">
          {statusMessage || "Processing..."}
        </div>
      </div>
    );
  }

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
    <div className="space-y-4">
      {initError && (
        <Alert variant="destructive">
          <AlertDescription>{initError}</AlertDescription>
        </Alert>
      )}
      <JobDetailsForm
        mode="edit"
        jobId={jobId}
        initialData={initialData}
        onComplete={handleComplete}
        onCancel={() => router.push(`/jobs/${jobId}`)}
      />
    </div>
  );
}
