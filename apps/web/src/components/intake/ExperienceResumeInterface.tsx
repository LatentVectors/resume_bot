"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
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
import {
  useResumeVersions,
  useCurrentResume,
  useResumeVersion,
  usePinResumeVersion,
  useUnpinResume,
  useCreateResumeVersion,
} from "@/lib/hooks/useResumes";
import { resumesAPI } from "@/lib/api/resumes";
import { VersionNavigation } from "@/components/intake/VersionNavigation";
import { MarkdownContent } from "@/components/intake/MarkdownContent";
import { MarkdownRenderer } from "@/components/intake/MarkdownRenderer";
import { ChatInterface } from "@/components/intake/ChatInterface";
import { ResumeEditor } from "@/components/resume/ResumeEditor";
import { PDFPreview } from "@/components/intake/PDFPreview";
import { IntakeStepHeader } from "@/components/intake/IntakeStepHeader";
import { toast } from "sonner";
import { workflowsAPI } from "@/lib/api/workflows";
import type { components } from "@/types/api";
import { pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`;

type ResumeData = components["schemas"]["ResumeData"];

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
  const [showUnsavedDialog, setShowUnsavedDialog] = useState(false);
  const [pendingVersionChange, setPendingVersionChange] = useState<
    number | null
  >(null);
  const [pendingNavigation, setPendingNavigation] = useState<
    (() => void) | null
  >(null);
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);
  const [isLoadingPdf, setIsLoadingPdf] = useState(false);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [chatMessages, setChatMessages] = useState<
    Array<{
      role: "user" | "assistant" | "tool";
      content: string;
      tool_calls?: Array<{ [key: string]: unknown }> | null;
      tool_call_id?: string | null;
    }>
  >([]);
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [quotaError, setQuotaError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);
  const [initializationError, setInitializationError] = useState<string | null>(
    null
  );
  const [gapAnalysis, setGapAnalysis] = useState<string | null>(null);
  const [stakeholderAnalysis, setStakeholderAnalysis] = useState<string | null>(
    null
  );

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
    }
  }, [selectedVersion, loadedVersionId, versions.length, user]);

  // Calculate dirty state
  const isDirty = useMemo(() => {
    if (!draftResume || !loadedVersionId || !selectedVersion) {
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
    const loadedJson = selectedVersion.resume_json;
    const currentJson = JSON.stringify(draftResume);
    return currentJson !== loadedJson;
  }, [draftResume, loadedVersionId, selectedVersion]);

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

        // Step 6: Load chat messages
        try {
          const messages = await jobsAPI.getIntakeSessionMessages(
            jobId,
            intakeSession.id,
            2
          );
          setChatMessages((messages || []) as typeof chatMessages);
        } catch (error) {
          console.error("Failed to load chat messages:", error);
          setChatMessages([]);
        }

        // Step 7: Set default selected version (latest or null)
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
      const achievementsByExp = new Map<
        number,
        components["schemas"]["AchievementResponse"][]
      >();

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

  // Handle sending chat message
  const handleSendMessage = useCallback(
    async (message: string) => {
      if (!intakeSession || !user?.id) {
        toast.error("Session or user information not available");
        return;
      }

      setIsChatLoading(true);
      setQuotaError(null);

      try {
        const workExperience = await formatWorkExperience();

        if (!gapAnalysis || !stakeholderAnalysis) {
          toast.error("Analyses not available. Please refresh the page.");
          return;
        }

        const apiMessages: components["schemas"]["ResumeChatMessage"][] =
          chatMessages.map((msg) => ({
            role: msg.role,
            content: msg.content,
            tool_calls: msg.tool_calls || null,
            tool_call_id: msg.tool_call_id || null,
          }));

        apiMessages.push({
          role: "user",
          content: message,
          tool_calls: null,
          tool_call_id: null,
        });

        const requestPayload: components["schemas"]["ResumeChatRequest"] = {
          messages: apiMessages,
          job_id: jobId,
          selected_version_id: selectedVersionId || null,
          gap_analysis: gapAnalysis,
          stakeholder_analysis: stakeholderAnalysis,
          work_experience: workExperience,
        };

        const response = await workflowsAPI.resumeChat(requestPayload);

        const aiMessage = response.message;
        const newVersionId = response.version_id;

        const assistantMessage: (typeof chatMessages)[0] = {
          role: "assistant",
          content:
            typeof aiMessage.content === "string" ? aiMessage.content : "",
          tool_calls: Array.isArray(aiMessage.tool_calls)
            ? aiMessage.tool_calls
            : null,
        };

        const updatedMessages = [...chatMessages, assistantMessage];
        setChatMessages(updatedMessages);

        try {
          await jobsAPI.saveIntakeSessionMessages(
            jobId,
            intakeSession.id,
            2,
            updatedMessages
          );
        } catch (error) {
          console.error("Failed to save messages:", error);
        }

        if (newVersionId) {
          setSelectedVersionId(newVersionId);
          window.location.reload();
        }
      } catch (error: unknown) {
        console.error("Failed to send message:", error);
        const err = error as { status?: number; detail?: string };

        if (err?.status === 429 || err?.detail?.includes("quota")) {
          setQuotaError("API quota exceeded. Please try again later.");
          setTimeout(() => {
            setQuotaError(null);
          }, 100);
        } else if (err?.status === 422) {
          toast.error(
            err?.detail || "Validation error. Please check your message."
          );
        } else {
          toast.error(
            err?.detail || "Failed to send message. Please try again."
          );
        }
      } finally {
        setIsChatLoading(false);
      }
    },
    [
      chatMessages,
      intakeSession,
      user?.id,
      jobId,
      selectedVersionId,
      formatWorkExperience,
      gapAnalysis,
      stakeholderAnalysis,
    ]
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

  // Handle download resume
  const handleDownloadResume = async () => {
    if (
      !selectedVersionId ||
      !canonicalVersionId ||
      selectedVersionId !== canonicalVersionId
    ) {
      toast.error("Can only download pinned versions");
      return;
    }
    try {
      const blob = await resumesAPI.downloadPDF(jobId, selectedVersionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      
      // Build filename matching Streamlit format: Resume - {company} - {title} - {name} - {yyyy_mm_dd}.pdf
      const sanitize = (value: string) => {
        return value
          .trim()
          .replace(/[/\\:*?"<>|]/g, "-")
          .replace(/\s+/g, " ");
      };
      
      const companyName = sanitize(job?.company_name || "Unknown Company");
      const jobTitle = sanitize(job?.job_title || "Unknown Title");
      
      // Parse resume_json to get name
      let fullName = "Unknown Name";
      try {
        const resumeData = selectedVersion?.resume_json ? JSON.parse(selectedVersion.resume_json) : null;
        fullName = sanitize(resumeData?.name || "Unknown Name");
      } catch {
        // Use default if parsing fails
      }
      
      // Format date as YYYY_MM_DD
      const now = new Date();
      const dateStr = `${now.getFullYear()}_${String(now.getMonth() + 1).padStart(2, "0")}_${String(now.getDate()).padStart(2, "0")}`;
      
      const filename = `Resume - ${companyName} - ${jobTitle} - ${fullName} - ${dateStr}.pdf`;
      
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
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

      const createPayload: components["schemas"]["ResumeCreate"] = {
        resume_json: JSON.stringify(draftResume),
        template_name: templateName,
        event_type: "save" as components["schemas"]["ResumeVersionEvent"],
        parent_version_id: selectedVersion?.id || null,
      };

      const version = await createVersion.mutateAsync({
        jobId,
        data: createPayload,
      });

      if (version.id) {
        setSelectedVersionId(version.id);
      }
      setLoadedVersionId(version.id || null);

      toast.success("Changes saved as new version!");

      refreshPdfPreview();
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
    }
    if (pendingNavigation) {
      pendingNavigation();
      setPendingNavigation(null);
    }
    setShowUnsavedDialog(false);
    setPendingVersionChange(null);
  };

  // Refresh PDF preview
  const refreshPdfPreview = useCallback(async () => {
    if (!selectedVersionId || !selectedVersion) {
      setPdfPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
      return;
    }

    setIsLoadingPdf(true);
    setPdfError(null);

    try {
      const resumeJson =
        isDirty && draftResume
          ? draftResume
          : (JSON.parse(selectedVersion.resume_json) as ResumeData);

      const templateName = selectedVersion.template_name || "resume_000.html";

      const blob = await resumesAPI.previewPDF(
        jobId,
        selectedVersionId,
        resumeJson,
        templateName
      );

      setPdfPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return URL.createObjectURL(blob);
      });
    } catch (error) {
      console.error("Failed to load PDF preview:", error);
      setPdfError("Failed to render PDF preview");
      setPdfPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return null;
      });
    } finally {
      setIsLoadingPdf(false);
    }
  }, [
    selectedVersionId,
    selectedVersion?.id,
    selectedVersion?.resume_json,
    selectedVersion?.template_name,
    isDirty,
    draftResume,
    jobId,
  ]);

  // Load PDF preview when version changes or after save
  useEffect(() => {
    if (selectedTab === "preview" && selectedVersionId && selectedVersion) {
      refreshPdfPreview();
    }
  }, [selectedTab, selectedVersionId, selectedVersion, refreshPdfPreview]);

  // Cleanup PDF URL on unmount
  useEffect(() => {
    return () => {
      if (pdfPreviewUrl) {
        URL.revokeObjectURL(pdfPreviewUrl);
      }
    };
  }, [pdfPreviewUrl]);

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
      toast.error(err?.detail || "Failed to proceed to next step. Please try again.");
    }
  };

  // Copy prompt handlers
  const handleCopyGapAnalysisPrompt = async () => {
    try {
      // Fetch the system prompt
      const { prompt: systemPrompt } = await promptsAPI.getPrompt("gap_analysis");
      
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
      const { prompt: systemPrompt } = await promptsAPI.getPrompt("stakeholder_analysis");
      
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
      const { prompt: systemPrompt } = await promptsAPI.getPrompt("resume_alignment_workflow");
      
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

  const columnHeight = "calc(100vh - 180px)";

  return (
    <div className="flex h-screen flex-col">
      {/* Header Row */}
      {showStepTitle && (
        <div className="flex items-center justify-between pt-3 pb-2">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold">
              Job Intake: Step 2 of 3 - Experience & Resume Development
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={isChatLoading}
            >
              Back
            </Button>
            <Button
              onClick={handleNext}
              disabled={isChatLoading}
            >
              Next
            </Button>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  disabled={isChatLoading}
                >
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
      <div className="flex-1">
        <div
          className="grid gap-6 md:grid-cols-[40%_1px_1fr]"
          style={{ height: columnHeight }}
        >
          {/* Left column: Chat interface (40%) */}
          {intakeSession && (
            <ChatInterface
              jobId={jobId}
              sessionId={intakeSession.id}
              messages={chatMessages}
              onMessagesChange={setChatMessages}
              onSendMessage={handleSendMessage}
              isLoading={isChatLoading}
              quotaError={quotaError}
              onQuotaErrorDismiss={() => setQuotaError(null)}
            />
          )}

          {/* Vertical separator */}
          <Separator orientation="vertical" />

          {/* Right column: Tabs interface */}
          <div className="flex flex-col overflow-hidden">
            <Tabs
              value={selectedTab}
              onValueChange={setSelectedTab}
              className="flex h-full flex-col"
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

              <div
                className="flex-1 overflow-y-auto p-4"
                style={{ height: "600px" }}
              >
                <TabsContent value="job" className="h-full">
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
                </TabsContent>

                <TabsContent value="gap-analysis" className="h-full">
                  <div className="h-full overflow-y-auto">
                    <MarkdownRenderer content={gapAnalysis || ""} />
                  </div>
                </TabsContent>

                <TabsContent value="stakeholder-analysis" className="h-full">
                  <div className="h-full overflow-y-auto">
                    <MarkdownRenderer content={stakeholderAnalysis || ""} />
                  </div>
                </TabsContent>

                <TabsContent value="content" className="h-full">
                  <div className="space-y-4">
                    {/* Version Navigation - Only show when NOT dirty */}
                    {!isDirty && versions.length > 0 && (
                      <VersionNavigation
                        versions={versions}
                        selectedVersionId={selectedVersionId}
                        canonicalVersionId={canonicalVersionId}
                        onVersionChange={handleVersionChange}
                        onPin={handlePin}
                        onUnpin={handleUnpin}
                        onCopyResume={handleCopyResume}
                        onDownloadResume={handleDownloadResume}
                      />
                    )}

                    {/* Save/Discard Buttons - Only show when dirty */}
                    {isDirty && (
                      <div className="flex items-center justify-end gap-2">
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

                    {/* Resume Editor */}
                    <div
                      className="overflow-y-auto"
                      style={{ height: "600px" }}
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
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="preview" className="h-full">
                  <div className="space-y-4">
                    {/* Version Navigation - Only show when NOT dirty */}
                    {!isDirty && versions.length > 0 && (
                      <VersionNavigation
                        versions={versions}
                        selectedVersionId={selectedVersionId}
                        canonicalVersionId={canonicalVersionId}
                        onVersionChange={handleVersionChange}
                        onPin={handlePin}
                        onUnpin={handleUnpin}
                        onCopyResume={handleCopyResume}
                        onDownloadResume={handleDownloadResume}
                      />
                    )}

                    {/* Save/Discard Buttons - Only show when dirty */}
                    {isDirty && (
                      <div className="flex items-center justify-end gap-2">
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

                    {/* PDF Preview */}
                    <div className="h-[600px] overflow-y-auto border rounded-lg p-4 bg-gray-50">
                      <PDFPreview
                        url={pdfPreviewUrl}
                        isLoading={isLoadingPdf}
                        error={pdfError}
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

// Helper function to format resume as text
function formatResumeAsText(resume: ResumeData): string {
  let text = `${resume.name}\n${resume.title}\n\n`;
  text += `Email: ${resume.email}\n`;
  if (resume.phone) text += `Phone: ${resume.phone}\n`;
  if (resume.linkedin_url) text += `LinkedIn: ${resume.linkedin_url}\n`;
  text += `\n${resume.professional_summary}\n\n`;

  if (resume.experience && resume.experience.length > 0) {
    text += "EXPERIENCE\n";
    resume.experience.forEach((exp) => {
      text += `\n${exp.title} at ${exp.company}\n`;
      text += `${exp.start_date} - ${exp.end_date || "Present"}\n`;
      if (exp.points) {
        exp.points.forEach((point) => {
          text += `• ${point}\n`;
        });
      }
    });
  }

  if (resume.education && resume.education.length > 0) {
    text += "\nEDUCATION\n";
    resume.education.forEach((edu) => {
      text += `\n${edu.degree} in ${edu.major}\n`;
      text += `${edu.institution} - ${edu.grad_date}\n`;
    });
  }

  if (resume.skills && resume.skills.length > 0) {
    text += "\nSKILLS\n";
    text += resume.skills.join(", ") + "\n";
  }

  if (resume.certifications && resume.certifications.length > 0) {
    text += "\nCERTIFICATIONS\n";
    resume.certifications.forEach((cert) => {
      text += `${cert.title} - ${cert.date}\n`;
    });
  }

  return text;
}
