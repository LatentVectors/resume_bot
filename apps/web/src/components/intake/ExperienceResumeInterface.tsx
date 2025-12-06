"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useMemo, useCallback } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { ScrollFadeContainer } from "@/components/ui/scroll-fade-container";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreVertical } from "lucide-react";
import { useJob } from "@/lib/hooks/useJobs";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useExperiences } from "@/lib/hooks/useExperiences";
import { useIntakeStore } from "@/lib/store/intake";
import { jobsAPI } from "@/lib/api/jobs";
import { experiencesAPI } from "@/lib/api/experiences";
import { promptsAPI } from "@/lib/api/prompts";
import { formatAllExperiences } from "@/lib/utils/formatExperiences";
import { formatResumeAsText } from "@/lib/utils/formatResume";
import {
  useResumeVersions,
  useCurrentResume,
  useResumeVersion,
  usePinResumeVersion,
  useUnpinResume,
  useCreateResumeVersion,
} from "@/lib/hooks/useResumes";
import {
  VersionActionMenu,
  VersionNavigation,
} from "@/components/intake/VersionNavigation";
import { MarkdownContent } from "@/components/intake/MarkdownContent";
import { MarkdownRenderer } from "@/components/intake/MarkdownRenderer";
import { ResumeChat } from "@/components/resume-chat/ResumeChat";
import { ResumeEditor } from "@/components/resume/ResumeEditor";
import { ResumePDFPreview } from "@/components/pdf/ResumePDFPreview";
import {
  usePdfGeneration,
  generateResumeFilename,
} from "@/lib/hooks/usePdfGeneration";
import { IntakeStepHeader } from "@/components/intake/IntakeStepHeader";
import { toast } from "sonner";
import type {
  Job,
  Achievement,
  ResumeVersionEvent,
  ResumeData,
} from "@resume/database/types";

interface ExperienceResumeInterfaceProps {
  jobId: number;
  showStepTitle?: boolean;
  showFooter?: boolean;
}

export function ExperienceResumeInterface({
  jobId,
  showStepTitle = true,
  showFooter = true,
}: ExperienceResumeInterfaceProps) {
  const router = useRouter();
  const { setCurrentStep, setSessionId } = useIntakeStore();

  const [selectedTab, setSelectedTab] = useState<string>("job");
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(
    null
  );
  const [loadedVersionId, setLoadedVersionId] = useState<number | null>(null);
  const [draftResume, setDraftResume] = useState<ResumeData | null>(null);
  const [loadedResumeJson, setLoadedResumeJson] = useState<string | null>(null);
  const [showUnsavedDialog, setShowUnsavedDialog] = useState(false);
  const [pendingVersionChange, setPendingVersionChange] = useState<
    number | null
  >(null);
  const [pendingNavigation, setPendingNavigation] = useState<
    (() => void) | null
  >(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [initializationError, setInitializationError] = useState<string | null>(
    null
  );
  const [gapAnalysis, setGapAnalysis] = useState<string | null>(null);
  const [stakeholderAnalysis, setStakeholderAnalysis] = useState<string | null>(
    null
  );
  const [resumeChatThreadId, setResumeChatThreadId] = useState<string | null>(
    null
  );
  const [pendingAgentVersion, setPendingAgentVersion] = useState(false);

  // Fetch job data
  const { data: job, isLoading: isLoadingJob, error: jobError } = useJob(jobId);

  // Fetch current user
  const {
    data: user,
    isLoading: isLoadingUser,
    error: userError,
  } = useCurrentUser();

  // Fetch user experiences
  const { data: experiences } = useExperiences(user?.id ?? 0);

  // Fetch intake session
  const {
    data: intakeSession,
    isLoading: isLoadingSession,
    error: sessionError,
  } = useQuery({
    queryKey: ["intake-session", jobId],
    queryFn: () => jobsAPI.getIntakeSession(jobId),
    enabled: !!jobId,
    retry: false,
  });

  // Fetch resume versions
  const {
    data: versions = [],
    isLoading: isLoadingVersions,
    error: versionsError,
  } = useResumeVersions(jobId);

  // Fetch current resume (canonical)
  const { data: currentResume } = useCurrentResume(jobId);

  // Fetch selected version
  const { data: selectedVersion } = useResumeVersion(
    jobId,
    selectedVersionId ?? 0
  );

  // Mutations
  const pinVersion = usePinResumeVersion();
  const unpinResume = useUnpinResume();
  const queryClient = useQueryClient();

  // Callback when agent creates a new resume version via tool call
  const handleResumeVersionCreated = useCallback(() => {
    setPendingAgentVersion(true);
    queryClient.invalidateQueries({ queryKey: ["resumes", jobId] });
  }, [queryClient, jobId]);
  const createVersion = useCreateResumeVersion();

  // Determine canonical version ID
  const canonicalVersionId = useMemo(() => {
    if (!versions || !currentResume) return null;
    for (const version of versions) {
      if (version.resume_json === currentResume.resume_json) {
        return version.id || null;
      }
    }
    return null;
  }, [versions, currentResume]);

  // Load draft from selected version
  useEffect(() => {
    if (selectedVersion && selectedVersion.id !== loadedVersionId) {
      try {
        const resumeData = JSON.parse(
          selectedVersion.resume_json
        ) as ResumeData;
        setDraftResume(resumeData);
        setLoadedVersionId(selectedVersion.id);
        // Store normalized JSON for accurate dirty comparison
        // (JSON.stringify may produce different output than the original database string)
        setLoadedResumeJson(JSON.stringify(resumeData));
      } catch (error) {
        console.error("Failed to parse resume JSON:", error);
        toast.error("Failed to load resume data");
      }
    } else if (!selectedVersion && versions.length === 0 && user) {
      // Initialize empty draft with user's basic info if no versions exist
      const emptyDraft: ResumeData = {
        name: `${user.first_name || ""} ${user.last_name || ""}`.trim() || "",
        email: user.email || "",
        phone: user.phone_number || "",
        linkedin_url: user.linkedin_url || "",
        title: "",
        professional_summary: "",
        experience: [],
        education: [],
        certifications: [],
        skills: [],
      };
      setDraftResume(emptyDraft);
      setLoadedVersionId(null);
      setLoadedResumeJson(JSON.stringify(emptyDraft));
    }
  }, [selectedVersion, loadedVersionId, versions.length, user]);

  // Auto-select latest version when agent creates a new one
  useEffect(() => {
    if (pendingAgentVersion && versions.length > 0) {
      const latestVersion = [...versions].sort((a, b) => {
        const indexA = a.version_index || 0;
        const indexB = b.version_index || 0;
        return indexB - indexA;
      })[0];
      if (latestVersion?.id) {
        setSelectedVersionId(latestVersion.id);
        setPendingAgentVersion(false);
      }
    }
  }, [pendingAgentVersion, versions]);

  // Calculate dirty state
  const isDirty = useMemo(() => {
    if (
      !draftResume ||
      !loadedVersionId ||
      !selectedVersion ||
      !loadedResumeJson
    ) {
      // If no loaded version, consider dirty if any content exists
      if (!loadedVersionId && draftResume) {
        return !!(
          draftResume.name ||
          draftResume.title ||
          draftResume.professional_summary ||
          (draftResume.experience && draftResume.experience.length > 0) ||
          (draftResume.education && draftResume.education.length > 0) ||
          (draftResume.certifications &&
            draftResume.certifications.length > 0) ||
          (draftResume.skills && draftResume.skills.length > 0)
        );
      }
      return false;
    }
    // If we're in a transitional state (switching versions), don't consider dirty
    // This happens when selectedVersion has loaded but the effect hasn't updated draftResume yet
    if (selectedVersion.id !== loadedVersionId) {
      return false;
    }
    // Compare against the normalized JSON we stored when loading
    // (avoids false positives from JSON serialization differences)
    const currentJson = JSON.stringify(draftResume);
    return currentJson !== loadedResumeJson;
  }, [draftResume, loadedVersionId, selectedVersion, loadedResumeJson]);

  const versionControlsDisabled = isDirty || createVersion.isPending;
  const isCurrentVersionPinned =
    canonicalVersionId !== null && selectedVersionId === canonicalVersionId;

  // Initialization sequence
  useEffect(() => {
    const initialize = async () => {
      setIsInitializing(true);
      setInitializationError(null);

      try {
        // Step 1: Fetch job data
        if (isLoadingJob) return;
        if (jobError || !job) {
          setInitializationError("Failed to load job data. Please try again.");
          setIsInitializing(false);
          return;
        }

        // Step 2: Fetch intake session
        if (isLoadingSession) return;
        if (sessionError || !intakeSession) {
          setInitializationError(
            "Failed to load intake session. Please try again."
          );
          setIsInitializing(false);
          return;
        }

        // Step 3: Validate gap_analysis and stakeholder_analysis exist
        const gapAnalysisText = intakeSession.gap_analysis
          ? (() => {
              try {
                const parsed = JSON.parse(intakeSession.gap_analysis);
                return typeof parsed === "string"
                  ? parsed
                  : intakeSession.gap_analysis;
              } catch {
                return intakeSession.gap_analysis;
              }
            })()
          : null;

        const stakeholderAnalysisText = intakeSession.stakeholder_analysis
          ? (() => {
              try {
                const parsed = JSON.parse(intakeSession.stakeholder_analysis);
                return typeof parsed === "string"
                  ? parsed
                  : intakeSession.stakeholder_analysis;
              } catch {
                return intakeSession.stakeholder_analysis;
              }
            })()
          : null;

        if (!gapAnalysisText || !stakeholderAnalysisText) {
          setInitializationError(
            "Unable to load analyses. Please restart intake flow."
          );
          setIsInitializing(false);
          return;
        }

        setGapAnalysis(gapAnalysisText);
        setStakeholderAnalysis(stakeholderAnalysisText);

        // Step 4: Fetch user data
        if (isLoadingUser) return;
        if (userError || !user) {
          setInitializationError("Failed to load user data. Please try again.");
          setIsInitializing(false);
          return;
        }

        // Step 5: Fetch versions list
        if (isLoadingVersions) return;
        if (versionsError) {
          console.error("Failed to load versions:", versionsError);
        }

        // Step 6: Set default selected version (latest or null)
        if (versions && versions.length > 0) {
          const latestVersion = [...versions].sort((a, b) => {
            const indexA = a.version_index || 0;
            const indexB = b.version_index || 0;
            return indexB - indexA;
          })[0];
          if (latestVersion?.id) {
            setSelectedVersionId(latestVersion.id);
          }
        }

        // Initialize session ID
        setSessionId(intakeSession.id.toString());

        // Initialize resume chat thread ID from job data if available
        if (job.resume_chat_thread_id) {
          setResumeChatThreadId(job.resume_chat_thread_id);
        }

        setIsInitializing(false);
      } catch (error) {
        console.error("Initialization error:", error);
        setInitializationError("Failed to initialize page. Please try again.");
        setIsInitializing(false);
      }
    };

    initialize();
  }, [
    jobId,
    job,
    isLoadingJob,
    jobError,
    intakeSession,
    isLoadingSession,
    sessionError,
    user,
    isLoadingUser,
    userError,
    versions,
    isLoadingVersions,
    versionsError,
    setSessionId,
  ]);

  // Format work experience for API
  const formatWorkExperience = useCallback(async () => {
    if (!user?.id) return "No work experience available.";
    try {
      const experiences = await experiencesAPI.list(user.id);
      const achievementsByExp = new Map<number, Achievement[]>();

      await Promise.all(
        experiences.map(async (exp) => {
          try {
            const achievements = await experiencesAPI.listAchievements(exp.id);
            achievementsByExp.set(exp.id, achievements);
          } catch (error) {
            console.error(
              `Failed to fetch achievements for experience ${exp.id}:`,
              error
            );
          }
        })
      );

      return formatAllExperiences(experiences, achievementsByExp);
    } catch (error) {
      console.error("Failed to format work experience:", error);
      return "No work experience available.";
    }
  }, [user?.id]);

  // Handle thread creation callback - persists thread_id to the Job record
  const handleThreadCreated = useCallback(
    async (threadId: string) => {
      try {
        await jobsAPI.update(jobId, { resume_chat_thread_id: threadId });
        setResumeChatThreadId(threadId);
      } catch (error) {
        console.error("Failed to persist thread ID:", error);
        toast.error("Failed to save chat thread. Messages may not persist.");
      }
    },
    [jobId]
  );

  const handleBack = () => {
    if (isDirty) {
      setPendingNavigation(() => () => {
        router.push(`/intake/${jobId}/details`);
      });
      setShowUnsavedDialog(true);
    } else {
      router.push(`/intake/${jobId}/details`);
    }
  };

  // Handle version change with dirty check
  const handleVersionChange = useCallback(
    (newVersionId: number | null) => {
      if (isDirty) {
        setPendingVersionChange(newVersionId);
        setShowUnsavedDialog(true);
      } else {
        setSelectedVersionId(newVersionId);
      }
    },
    [isDirty]
  );

  // Handle pin/unpin
  const handlePin = async (versionId: number) => {
    try {
      await pinVersion.mutateAsync({ jobId, versionId });
      toast.success("Pinned canonical resume.");
    } catch (error: unknown) {
      console.error("Failed to pin version:", error);
      const err = error as { status?: number; detail?: string };
      if (err?.status === 422) {
        toast.error(err?.detail || "Validation error. Please check your data.");
      } else {
        toast.error(err?.detail || "Failed to pin resume");
      }
    }
  };

  const handleUnpin = async () => {
    try {
      await unpinResume.mutateAsync({ jobId });
      toast.success("Unpinned resume.");
    } catch (error: unknown) {
      console.error("Failed to unpin resume:", error);
      const err = error as { status?: number; detail?: string };
      if (err?.status === 422) {
        toast.error(err?.detail || "Validation error. Please check your data.");
      } else {
        toast.error(err?.detail || "Failed to unpin resume");
      }
    }
  };

  // Handle copy resume
  const handleCopyResume = () => {
    if (!draftResume) return;
    const text = formatResumeAsText(draftResume);
    navigator.clipboard.writeText(text);
    toast.success("Resume text copied to clipboard");
  };

  // PDF generation hook
  const { downloadPdf, isGenerating: isGeneratingPdf } = usePdfGeneration();

  // Handle download resume
  const handleDownloadResume = async () => {
    if (!draftResume) {
      toast.error("No resume data to download");
      return;
    }

    try {
      const filename = generateResumeFilename(
        job?.company_name,
        job?.job_title,
        draftResume.name
      );
      await downloadPdf(draftResume, filename);
      toast.success("Resume downloaded successfully");
    } catch (error) {
      console.error("Failed to download PDF:", error);
      toast.error("Failed to download resume");
    }
  };

  // Handle unsaved changes dialog
  const handleDiscardAndChange = () => {
    if (pendingVersionChange !== null) {
      setSelectedVersionId(pendingVersionChange);
      setDraftResume(null);
      setLoadedVersionId(null);
      setLoadedResumeJson(null);
    }
    if (pendingNavigation) {
      pendingNavigation();
      setPendingNavigation(null);
    }
    setShowUnsavedDialog(false);
    setPendingVersionChange(null);
  };

  // Update draft resume
  const updateDraftResume = useCallback(
    (updater: (prev: ResumeData) => ResumeData) => {
      setDraftResume((prev) => (prev ? updater(prev) : null));
    },
    []
  );

  // Handle save
  const handleSave = async () => {
    if (!draftResume) {
      toast.error("No resume data to save");
      return;
    }

    try {
      const templateName = selectedVersion?.template_name || "resume_000.html";

      const version = await createVersion.mutateAsync({
        jobId,
        data: {
          resume_json: JSON.stringify(draftResume),
          template_name: templateName,
          event_type: "save" as ResumeVersionEvent,
          parent_version_id: selectedVersion?.id || null,
          created_by_user_id: user!.id,
        },
      });

      if (version.id) {
        setSelectedVersionId(version.id);
      }
      setLoadedVersionId(version.id || null);
      // Update the normalized JSON to match the saved draft (clears dirty state)
      setLoadedResumeJson(JSON.stringify(draftResume));

      toast.success("Changes saved as new version!");
    } catch (error: unknown) {
      console.error("Failed to save resume:", error);
      const err = error as { status?: number; detail?: string };
      if (err?.status === 422) {
        const errorMessage =
          err?.detail || "Validation error. Please check your resume data.";
        toast.error(errorMessage);
      } else {
        toast.error(err?.detail || "Failed to save resume. Please try again.");
      }
    }
  };

  // Handle discard
  const handleDiscard = useCallback(() => {
    if (selectedVersion && loadedVersionId === selectedVersion.id) {
      try {
        const resumeData = JSON.parse(
          selectedVersion.resume_json
        ) as ResumeData;
        setDraftResume(resumeData);
      } catch (error) {
        console.error("Failed to parse resume JSON:", error);
        toast.error("Failed to discard changes");
      }
    } else if (!loadedVersionId && user) {
      const emptyDraft: ResumeData = {
        name: `${user.first_name || ""} ${user.last_name || ""}`.trim() || "",
        email: user.email || "",
        phone: user.phone_number || "",
        linkedin_url: user.linkedin_url || "",
        title: "",
        professional_summary: "",
        experience: [],
        education: [],
        certifications: [],
        skills: [],
      };
      setDraftResume(emptyDraft);
    }
  }, [selectedVersion, loadedVersionId, user]);

  const handleSaveAndChange = async () => {
    await handleSave();
    if (pendingVersionChange !== null) {
      setSelectedVersionId(pendingVersionChange);
      setDraftResume(null);
      setLoadedVersionId(null);
      setLoadedResumeJson(null);
    }
    if (pendingNavigation) {
      pendingNavigation();
      setPendingNavigation(null);
    }
    setShowUnsavedDialog(false);
    setPendingVersionChange(null);
  };

  const handleNext = async () => {
    try {
      if (intakeSession) {
        await jobsAPI.updateIntakeSession(jobId, {
          current_step: 3,
          step_completed: 2,
        });
      }
      setCurrentStep("proposals");
      router.push(`/intake/${jobId}/proposals`);
    } catch (error: unknown) {
      console.error("Failed to proceed to next step:", error);
      const err = error as { detail?: string };
      toast.error(
        err?.detail || "Failed to proceed to next step. Please try again."
      );
    }
  };

  // Copy prompt handlers
  const handleCopyGapAnalysisPrompt = async () => {
    try {
      // Fetch the system prompt
      const { prompt: systemPrompt } = await promptsAPI.getPrompt(
        "gap_analysis"
      );

      // Get job description
      const jobDescription = job?.job_description || "";

      // Format work experience
      const workExperience = await formatWorkExperience();

      // Build the complete prompt with XML tags
      const completePrompt = `${systemPrompt}

<job_description>
${jobDescription}
</job_description>

<work_experience>
${workExperience}
</work_experience>`;

      // Copy to clipboard
      await navigator.clipboard.writeText(completePrompt);
      toast.success("Gap analysis prompt copied to clipboard!");
    } catch (error) {
      console.error("Failed to copy gap analysis prompt:", error);
      toast.error("Failed to copy prompt. Please try again.");
    }
  };

  const handleCopyStakeholderAnalysisPrompt = async () => {
    try {
      // Fetch the system prompt
      const { prompt: systemPrompt } = await promptsAPI.getPrompt(
        "stakeholder_analysis"
      );

      // Get job description
      const jobDescription = job?.job_description || "";

      // Format work experience
      const workExperience = await formatWorkExperience();

      // Build the complete prompt with XML tags
      const completePrompt = `${systemPrompt}

<job_description>
${jobDescription}
</job_description>

<work_experience>
${workExperience}
</work_experience>`;

      // Copy to clipboard
      await navigator.clipboard.writeText(completePrompt);
      toast.success("Stakeholder analysis prompt copied to clipboard!");
    } catch (error) {
      console.error("Failed to copy stakeholder analysis prompt:", error);
      toast.error("Failed to copy prompt. Please try again.");
    }
  };

  const handleCopyResumeWorkflowPrompt = async () => {
    try {
      // Fetch the system prompt
      const { prompt: systemPrompt } = await promptsAPI.getPrompt(
        "resume_alignment_workflow"
      );

      // Get job description
      const jobDescription = job?.job_description || "";

      // Format work experience
      const workExperience = await formatWorkExperience();

      // Build the complete prompt with XML tags (gap_analysis and stakeholder_analysis empty)
      const completePrompt = `${systemPrompt}

<job_description>
${jobDescription}
</job_description>

<work_experience>
${workExperience}
</work_experience>

<gap_analysis>

</gap_analysis>

<stakeholder_analysis>

</stakeholder_analysis>`;

      // Copy to clipboard
      await navigator.clipboard.writeText(completePrompt);
      toast.success("Resume workflow prompt copied to clipboard!");
    } catch (error) {
      console.error("Failed to copy resume workflow prompt:", error);
      toast.error("Failed to copy prompt. Please try again.");
    }
  };

  // Show loading spinner during initialization
  if (isInitializing) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </div>
    );
  }

  // Show error if initialization failed
  if (initializationError) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <Alert className="max-w-md" variant="destructive">
          <AlertDescription>{initializationError}</AlertDescription>
        </Alert>
        {initializationError.includes("analyses") ? (
          <Button
            onClick={() => router.push(`/intake/${jobId}/details`)}
            variant="outline"
          >
            Go to Step 1
          </Button>
        ) : (
          <Button onClick={() => router.push("/jobs")} variant="outline">
            Back to Jobs
          </Button>
        )}
      </div>
    );
  }

  // Ensure we have required data
  if (!job || !user || !intakeSession) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <Alert className="max-w-md" variant="destructive">
          <AlertDescription>
            Missing required data. Please try again.
          </AlertDescription>
        </Alert>
        <Button onClick={() => router.push("/jobs")} variant="outline">
          Back to Jobs
        </Button>
      </div>
    );
  }

  // Validate analyses exist
  if (!gapAnalysis || !stakeholderAnalysis) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <Alert className="max-w-md" variant="destructive">
          <AlertDescription>
            Unable to load analyses. Please restart intake flow.
          </AlertDescription>
        </Alert>
        <Button
          onClick={() => router.push(`/intake/${jobId}/details`)}
          variant="outline"
        >
          Go to Step 1
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-64px)] overflow-hidden">
      {/* Header Row */}
      {showStepTitle && (
        <div className="flex items-center justify-between pt-3 pb-2">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold">
              Job Intake: Step 2 of 3 - Experience & Resume Development
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleBack}>
              Back
            </Button>
            <Button onClick={handleNext}>Next</Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon">
                  <MoreVertical className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleCopyGapAnalysisPrompt}>
                  Copy Gap Analysis Prompt
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleCopyStakeholderAnalysisPrompt}>
                  Copy Stakeholder Analysis Prompt
                </DropdownMenuItem>
                <DropdownMenuItem onClick={handleCopyResumeWorkflowPrompt}>
                  Copy Resume Workflow Prompt
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      )}

      {/* Two-column grid layout */}
      <div className="flex-1 min-h-0 pb-6">
        <div className="grid gap-0 md:grid-cols-[40%_1px_1fr] h-full">
          {/* Left column: Chat interface (40%) */}
          <div className="h-full overflow-hidden">
            {intakeSession && user && (
              <ResumeChat
                jobId={jobId}
                initialThreadId={resumeChatThreadId}
                onThreadCreated={handleThreadCreated}
                onResumeVersionCreated={handleResumeVersionCreated}
                context={{
                  job_id: jobId,
                  user_id: user.id,
                  gap_analysis: gapAnalysis || "",
                  stakeholder_analysis: stakeholderAnalysis || "",
                  work_experience: "", // Will be populated on first message
                  job_description: job?.job_description || "",
                  selected_version_id: selectedVersionId,
                  template_name:
                    selectedVersion?.template_name || "resume_000.html",
                  parent_version_id: selectedVersionId,
                }}
              />
            )}
          </div>

          {/* Vertical separator */}
          <Separator orientation="vertical" />

          {/* Right column: Tabs interface */}
          <div className="flex flex-col overflow-hidden pl-6 min-h-0">
            <Tabs
              value={selectedTab}
              onValueChange={setSelectedTab}
              className="flex h-full min-h-0 flex-col"
            >
              <div className="px-4 py-2">
                <TabsList>
                  <TabsTrigger value="job">Job</TabsTrigger>
                  <TabsTrigger value="gap-analysis">Gap Analysis</TabsTrigger>
                  <TabsTrigger value="stakeholder-analysis">
                    Stakeholder Analysis
                  </TabsTrigger>
                  <TabsTrigger value="content">Content</TabsTrigger>
                  <TabsTrigger value="preview">Preview</TabsTrigger>
                </TabsList>
              </div>

              <div className="flex-1 min-h-0 overflow-hidden">
                <TabsContent value="job" className="h-full">
                  <ScrollFadeContainer
                    className="h-full"
                    scrollClassName="px-4 pb-4 pt-0"
                    topGradientHeight={48}
                    bottomGradientHeight={96}
                    fadeThreshold={120}
                  >
                    <div className="space-y-4">
                      <div>
                        <strong>{job.job_title || "No title"}</strong> at{" "}
                        <strong>{job.company_name || "No company"}</strong>
                      </div>
                      {job.job_description ? (
                        <MarkdownContent content={job.job_description} />
                      ) : (
                        <Alert>
                          <AlertDescription>
                            No job description available.
                          </AlertDescription>
                        </Alert>
                      )}
                    </div>
                  </ScrollFadeContainer>
                </TabsContent>

                <TabsContent value="gap-analysis" className="h-full">
                  <ScrollFadeContainer
                    className="h-full"
                    scrollClassName="px-4 pb-4 pt-0"
                    topGradientHeight={48}
                    bottomGradientHeight={96}
                    fadeThreshold={120}
                  >
                    <MarkdownRenderer content={gapAnalysis || ""} />
                  </ScrollFadeContainer>
                </TabsContent>

                <TabsContent value="stakeholder-analysis" className="h-full">
                  <ScrollFadeContainer
                    className="h-full"
                    scrollClassName="px-4 pb-4 pt-0"
                    topGradientHeight={48}
                    bottomGradientHeight={96}
                    fadeThreshold={120}
                  >
                    <MarkdownRenderer content={stakeholderAnalysis || ""} />
                  </ScrollFadeContainer>
                </TabsContent>

                <TabsContent value="content" className="h-full">
                  <div className="flex h-full min-h-0 flex-col gap-4">
                    <div className="sticky top-0 z-20 bg-background">
                      <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
                        {versions.length > 0 && (
                          <VersionNavigation
                            versions={versions}
                            selectedVersionId={selectedVersionId}
                            canonicalVersionId={canonicalVersionId}
                            onVersionChange={handleVersionChange}
                            onPin={handlePin}
                            onUnpin={handleUnpin}
                            disabled={versionControlsDisabled}
                            className="flex-wrap"
                          />
                        )}
                        <div className="flex flex-wrap items-center gap-2">
                          <Button
                            variant="outline"
                            onClick={handleDiscard}
                            disabled={!isDirty || createVersion.isPending}
                          >
                            Discard
                          </Button>
                          <Button
                            onClick={handleSave}
                            disabled={!isDirty || createVersion.isPending}
                          >
                            Save
                          </Button>
                          <VersionActionMenu
                            disabled={versionControlsDisabled}
                            isPinned={isCurrentVersionPinned}
                            onCopyResume={handleCopyResume}
                            onDownloadResume={handleDownloadResume}
                          />
                        </div>
                      </div>
                    </div>

                    <ScrollFadeContainer
                      className="flex-1 min-h-0"
                      scrollClassName="pb-4 px-4 pt-0"
                      topGradientHeight={48}
                      bottomGradientHeight={96}
                      fadeThreshold={120}
                    >
                      {draftResume ? (
                        <ResumeEditor
                          resumeData={draftResume}
                          updateResume={updateDraftResume}
                          readOnly={false}
                        />
                      ) : (
                        <div className="text-muted-foreground p-4">
                          Loading resume data...
                        </div>
                      )}
                    </ScrollFadeContainer>
                  </div>
                </TabsContent>

                <TabsContent value="preview" className="h-full">
                  <div className="flex h-full min-h-0 flex-col gap-4">
                    <div className="sticky top-0 z-20 bg-background">
                      {!isDirty && versions.length > 0 && (
                        <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
                          <VersionNavigation
                            versions={versions}
                            selectedVersionId={selectedVersionId}
                            canonicalVersionId={canonicalVersionId}
                            onVersionChange={handleVersionChange}
                            onPin={handlePin}
                            onUnpin={handleUnpin}
                            disabled={versionControlsDisabled}
                            className="flex-wrap"
                          />
                          <VersionActionMenu
                            disabled={versionControlsDisabled}
                            isPinned={isCurrentVersionPinned}
                            onCopyResume={handleCopyResume}
                            onDownloadResume={handleDownloadResume}
                          />
                        </div>
                      )}

                      {isDirty && (
                        <div className="flex items-center justify-end gap-2 pb-2">
                          <Button
                            variant="outline"
                            onClick={handleDiscard}
                            disabled={createVersion.isPending}
                          >
                            Discard
                          </Button>
                          <Button
                            onClick={handleSave}
                            disabled={createVersion.isPending}
                          >
                            Save
                          </Button>
                        </div>
                      )}
                    </div>

                    <div className="flex-1 min-h-0 px-4 pb-4">
                      <ResumePDFPreview
                        resumeData={draftResume}
                        className="h-full"
                      />
                    </div>
                  </div>
                </TabsContent>
              </div>
            </Tabs>
          </div>
        </div>
      </div>

      {/* Unsaved Changes Dialog */}
      {showUnsavedDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="rounded-lg bg-background p-6 shadow-lg">
            <h3 className="mb-2 text-lg font-semibold">Unsaved Changes</h3>
            <p className="mb-4 text-sm text-muted-foreground">
              You have unsaved changes. What would you like to do?
            </p>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => {
                  setShowUnsavedDialog(false);
                  setPendingVersionChange(null);
                }}
              >
                Cancel
              </Button>
              <Button variant="outline" onClick={handleDiscardAndChange}>
                Discard Changes
              </Button>
              <Button onClick={handleSaveAndChange}>Save & Continue</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
