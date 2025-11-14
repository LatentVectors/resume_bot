"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useJob } from "@/lib/hooks/useJobs";
import { useExperiences } from "@/lib/hooks/useExperiences";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useIntakeStore } from "@/lib/store/intake";
import { jobsAPI } from "@/lib/api/jobs";
import { workflowsAPI } from "@/lib/api/workflows";
import type { components } from "@/types/api";

type GapAnalysisResponse = components["schemas"]["GapAnalysisResponse"];
type ResumeGenerationResponse = components["schemas"]["ResumeGenerationResponse"];

export default function IntakeExperiencePage() {
  const params = useParams();
  const router = useRouter();
  const jobId = parseInt(params.jobId as string, 10);
  const { setCurrentStep, setExperienceSelection, setSessionId } =
    useIntakeStore();

  const [selectedExperienceIds, setSelectedExperienceIds] = useState<number[]>(
    []
  );
  const [gapAnalysisResult, setGapAnalysisResult] =
    useState<GapAnalysisResponse | null>(null);

  // Fetch job data
  const { data: job, isLoading: isLoadingJob } = useJob(jobId);

  // Fetch current user
  const { data: user } = useCurrentUser();

  // Fetch user experiences
  const { data: experiences, isLoading: isLoadingExperiences } =
    useExperiences(user?.id ?? 0);

  // Fetch intake session
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

  // Initialize selected experiences from store
  useEffect(() => {
    const store = useIntakeStore.getState();
    if (store.experienceSelection?.selectedExperienceIds) {
      setSelectedExperienceIds(store.experienceSelection.selectedExperienceIds);
    }
  }, []);

  // Gap analysis mutation
  const gapAnalysisMutation = useMutation({
    mutationFn: (request: {
      job_description: string;
      experience_ids: number[];
    }) => {
      return workflowsAPI.gapAnalysis({
        job_description: request.job_description,
        experience_ids: request.experience_ids,
      });
    },
    onSuccess: (data) => {
      setGapAnalysisResult(data);
      // Update session with gap analysis
      if (intakeSession) {
        jobsAPI.updateIntakeSession(jobId, {
          gap_analysis: JSON.stringify(data),
        });
      }
    },
  });

  // Resume generation mutation
  const resumeGenerationMutation = useMutation({
    mutationFn: (request: {
      job_id: number;
      experience_ids: number[];
    }) => {
      if (!user?.id) {
        throw new Error("User not found");
      }
      return workflowsAPI.resumeGeneration({
        user_id: user.id,
        request: {
          job_id: request.job_id,
          experience_ids: request.experience_ids,
        },
      });
    },
    onSuccess: async () => {
      // Update session to mark step 2 as completed and move to step 3
      if (intakeSession) {
        await jobsAPI.updateIntakeSession(jobId, {
          current_step: 3,
          step_completed: 2,
        });
      }

      // Update Zustand store
      setExperienceSelection({
        selectedExperienceIds,
        gapAnalysisResults: gapAnalysisResult,
      });
      setCurrentStep("proposals");

      // Navigate to proposals step
      router.push(`/intake/${jobId}/proposals`);
    },
  });

  const handleExperienceToggle = (experienceId: number) => {
    setSelectedExperienceIds((prev) =>
      prev.includes(experienceId)
        ? prev.filter((id) => id !== experienceId)
        : [...prev, experienceId]
    );
  };

  const handleRunGapAnalysis = () => {
    if (selectedExperienceIds.length === 0) {
      alert("Please select at least one experience");
      return;
    }
    if (!job?.job_description) {
      alert("Job description is required for gap analysis");
      return;
    }
    gapAnalysisMutation.mutate({
      job_description: job.job_description,
      experience_ids: selectedExperienceIds,
    });
  };

  const handleGenerateResume = () => {
    if (selectedExperienceIds.length === 0) {
      alert("Please select at least one experience");
      return;
    }
    resumeGenerationMutation.mutate({
      job_id: jobId,
      experience_ids: selectedExperienceIds,
    });
  };

  if (isLoadingJob || isLoadingExperiences) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!job || !user) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <div className="text-destructive">
          {!job ? "Job not found" : "User not found"}
        </div>
        <Button onClick={() => router.push("/jobs")} variant="outline">
          Back to Jobs
        </Button>
      </div>
    );
  }

  const hasNoExperiences = !experiences || experiences.length === 0;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Select Experiences</CardTitle>
          <CardDescription>
            Choose the experiences you want to include in your resume for this
            job application.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {hasNoExperiences ? (
            <Alert>
              <AlertDescription>
                You don&apos;t have any experiences yet. Please add experiences
                in your profile first.
              </AlertDescription>
            </Alert>
          ) : (
            <div className="space-y-3">
              {experiences.map((experience) => (
                <div
                  key={experience.id}
                  className="flex items-start space-x-3 rounded-lg border p-4"
                >
                  <Checkbox
                    id={`experience-${experience.id}`}
                    checked={selectedExperienceIds.includes(experience.id)}
                    onCheckedChange={() =>
                      handleExperienceToggle(experience.id)
                    }
                  />
                  <Label
                    htmlFor={`experience-${experience.id}`}
                    className="flex-1 cursor-pointer space-y-1"
                  >
                    <div className="font-medium">
                      {experience.role_title} at {experience.company_name}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {experience.start_date} - {experience.end_date || "Present"}
                    </div>
                    {experience.role_overview && (
                      <div className="text-sm text-muted-foreground line-clamp-2">
                        {experience.role_overview}
                      </div>
                    )}
                  </Label>
                </div>
              ))}
            </div>
          )}

          <div className="flex gap-4">
            <Button
              onClick={handleRunGapAnalysis}
              disabled={
                selectedExperienceIds.length === 0 ||
                gapAnalysisMutation.isPending
              }
              variant="outline"
            >
              {gapAnalysisMutation.isPending
                ? "Running Analysis..."
                : "Run Gap Analysis"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {gapAnalysisResult && (
        <Card>
          <CardHeader>
            <CardTitle>Gap Analysis Results</CardTitle>
            <CardDescription>
              Analysis of how your experiences align with the job requirements.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg bg-muted p-4">
              <div className="whitespace-pre-wrap text-sm">
                {gapAnalysisResult.analysis}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Generate Resume</CardTitle>
          <CardDescription>
            Once you&apos;ve selected experiences and reviewed the gap analysis,
            generate your resume to proceed to the next step.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button
            onClick={handleGenerateResume}
            disabled={
              selectedExperienceIds.length === 0 ||
              resumeGenerationMutation.isPending
            }
            className="w-full"
          >
            {resumeGenerationMutation.isPending
              ? "Generating Resume..."
              : "Generate Resume & Continue"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

