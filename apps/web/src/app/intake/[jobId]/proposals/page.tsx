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
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useJob } from "@/lib/hooks/useJobs";
import { useExperiences } from "@/lib/hooks/useExperiences";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useIntakeStore } from "@/lib/store/intake";
import { jobsAPI } from "@/lib/api/jobs";
import { experiencesAPI } from "@/lib/api/experiences";
import type { components } from "@/types/api";

type ProposalResponse = components["schemas"]["ProposalResponse"];

export default function IntakeProposalsPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = parseInt(params.jobId as string, 10);
  const { clearIntake } = useIntakeStore();

  const [proposals, setProposals] = useState<ProposalResponse[]>([]);

  // Fetch job data
  const { data: job, isLoading: isLoadingJob } = useJob(jobId);

  // Fetch current user
  const { data: user } = useCurrentUser();

  // Fetch user experiences
  const { data: experiences } = useExperiences(user?.id ?? 0);

  // Fetch intake session
  const { data: intakeSession } = useQuery({
    queryKey: ["intake-session", jobId],
    queryFn: () => jobsAPI.getIntakeSession(jobId),
    enabled: !!jobId,
    retry: false,
  });

  // Fetch all proposals for the session
  const { data: allProposals, isLoading: isLoadingProposals } = useQuery({
    queryKey: ["proposals", intakeSession?.id],
    queryFn: async () => {
      if (!intakeSession?.id || !experiences) {
        return [];
      }

      // Fetch proposals for each experience
      const proposalPromises = experiences.map((exp) =>
        experiencesAPI.listProposals(exp.id, intakeSession.id)
      );
      const proposalArrays = await Promise.all(proposalPromises);
      return proposalArrays.flat();
    },
    enabled: !!intakeSession?.id && !!experiences && experiences.length > 0,
  });

  // Sync proposals state with fetched data
  // Note: This is a valid use case for syncing server state to local state for optimistic updates
  useEffect(() => {
    if (allProposals) {
      // Use setTimeout to avoid synchronous setState in effect
      const timeoutId = setTimeout(() => {
        setProposals(allProposals);
      }, 0);
      return () => clearTimeout(timeoutId);
    }
  }, [allProposals]);

  // Accept proposal mutation
  const acceptProposalMutation = useMutation({
    mutationFn: (proposalId: number) =>
      experiencesAPI.acceptProposal(proposalId),
    onSuccess: (_, proposalId) => {
      // Update local state
      setProposals((prev) =>
        prev.map((p) =>
          p.id === proposalId ? { ...p, status: "accepted" } : p
        )
      );
    },
  });

  // Reject proposal mutation
  const rejectProposalMutation = useMutation({
    mutationFn: (proposalId: number) =>
      experiencesAPI.rejectProposal(proposalId),
    onSuccess: (_, proposalId) => {
      // Update local state
      setProposals((prev) =>
        prev.map((p) =>
          p.id === proposalId ? { ...p, status: "rejected" } : p
        )
      );
    },
  });

  const handleAcceptProposal = (proposalId: number) => {
    acceptProposalMutation.mutate(proposalId);
  };

  const handleRejectProposal = (proposalId: number) => {
    rejectProposalMutation.mutate(proposalId);
  };

  const handleAcceptAll = () => {
    const pendingProposals = proposals.filter((p) => p.status === "pending");
    pendingProposals.forEach((p) => {
      acceptProposalMutation.mutate(p.id);
    });
  };

  const handleComplete = async () => {
    if (!intakeSession) return;

    try {
      // Mark step 3 as completed and complete the session
      await jobsAPI.updateIntakeSession(jobId, {
        current_step: 3,
        step_completed: 3,
      });

      // Clear intake state
      clearIntake();

      // Navigate to job detail page
      router.push(`/jobs/${jobId}`);
    } catch (error) {
      console.error("Failed to complete intake:", error);
    }
  };

  if (isLoadingJob || isLoadingProposals) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">Loading proposals...</div>
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

  const pendingProposals = proposals.filter((p) => p.status === "pending");
  const hasProposals = proposals.length > 0;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Experience Proposals</CardTitle>
          <CardDescription>
            Review and accept or reject AI-generated proposals to update your
            experiences based on the job requirements.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!hasProposals ? (
            <Alert>
              <AlertDescription>
                No proposals found. Proposals are generated during the resume
                generation process in the previous step.
              </AlertDescription>
            </Alert>
          ) : (
            <>
              {pendingProposals.length > 0 && (
                <div className="flex justify-end">
                  <Button
                    onClick={handleAcceptAll}
                    disabled={acceptProposalMutation.isPending}
                    variant="outline"
                  >
                    Accept All Pending
                  </Button>
                </div>
              )}

              <div className="space-y-4">
                {proposals.map((proposal) => {
                  const experience = experiences?.find(
                    (e) => e.id === proposal.experience_id
                  );
                  const isPending = proposal.status === "pending";
                  const isAccepted = proposal.status === "accepted";
                  const isRejected = proposal.status === "rejected";

                  return (
                    <Card key={proposal.id}>
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <div className="space-y-1">
                            <CardTitle className="text-lg">
                              {proposal.proposal_type === "role_overview_update"
                                ? "Role Overview Update"
                                : proposal.proposal_type ===
                                    "achievement_add" ||
                                  proposal.proposal_type ===
                                    "achievement_update" ||
                                  proposal.proposal_type ===
                                    "achievement_delete"
                                ? "Achievement Proposal"
                                : "Other Update"}
                            </CardTitle>
                            {experience && (
                              <CardDescription>
                                For: {experience.job_title} at{" "}
                                {experience.company_name}
                              </CardDescription>
                            )}
                          </div>
                          <Badge
                            variant={
                              isAccepted
                                ? "default"
                                : isRejected
                                ? "secondary"
                                : "outline"
                            }
                          >
                            {proposal.status}
                          </Badge>
                        </div>
                      </CardHeader>
                      <CardContent className="space-y-4">
                        <div className="space-y-2">
                          <div className="text-sm font-medium">
                            Proposed Content:
                          </div>
                          <div className="rounded-lg bg-muted p-4">
                            <p className="text-sm whitespace-pre-wrap">
                              {proposal.proposed_content}
                            </p>
                          </div>
                        </div>

                        {proposal.original_proposed_content && (
                          <div className="space-y-2">
                            <div className="text-sm font-medium">
                              Original Content:
                            </div>
                            <div className="rounded-lg bg-muted/50 p-4">
                              <p className="text-sm whitespace-pre-wrap text-muted-foreground">
                                {proposal.original_proposed_content}
                              </p>
                            </div>
                          </div>
                        )}

                        {isPending && (
                          <div className="flex gap-2">
                            <Button
                              onClick={() => handleAcceptProposal(proposal.id)}
                              disabled={acceptProposalMutation.isPending}
                              size="sm"
                            >
                              Accept
                            </Button>
                            <Button
                              onClick={() => handleRejectProposal(proposal.id)}
                              disabled={rejectProposalMutation.isPending}
                              variant="outline"
                              size="sm"
                            >
                              Reject
                            </Button>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Complete Intake</CardTitle>
          <CardDescription>
            Once you&apos;ve reviewed all proposals, complete the intake
            workflow to finish setting up this job application.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={handleComplete} className="w-full" size="lg">
            Complete Intake Workflow
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
