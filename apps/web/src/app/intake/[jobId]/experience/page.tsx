"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { Copy } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useJob } from "@/lib/hooks/useJobs";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useExperiences } from "@/lib/hooks/useExperiences";
import { useIntakeStore } from "@/lib/store/intake";
import { jobsAPI } from "@/lib/api/jobs";
import { experiencesAPI } from "@/lib/api/experiences";
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
import { ChatInterface } from "@/components/intake/ChatInterface";
import { ResumeEditor } from "@/components/resume/ResumeEditor";
import { toast } from "sonner";
import { workflowsAPI } from "@/lib/api/workflows";
import type { components } from "@/types/api";
import { Document, Page, pdfjs } from "react-pdf";
import "react-pdf/dist/Page/AnnotationLayer.css";
import "react-pdf/dist/Page/TextLayer.css";

// Set up PDF.js worker
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

type ResumeData = components["schemas"]["ResumeData"];

export default function IntakeExperiencePage() {
  const params = useParams();
  const router = useRouter();
  const jobId = parseInt(params.jobId as string, 10);
  const { setCurrentStep, setSessionId } = useIntakeStore();

  const [isCopyingContext, setIsCopyingContext] = useState(false);
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
  const [isNextLoading, setIsNextLoading] = useState(false);
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

  // Note: Version selection is now handled in initialization sequence

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

  // Initialization sequence (per spec order)
  useEffect(() => {
    const initialize = async () => {
      setIsInitializing(true);
      setInitializationError(null);

      try {
        // Step 1: Fetch job data (already fetched via useJob hook)
        if (isLoadingJob) return;
        if (jobError || !job) {
          setInitializationError("Failed to load job data. Please try again.");
          setIsInitializing(false);
          return;
        }

        // Step 2: Fetch intake session (already fetched via useQuery)
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

        // Step 4: Fetch user data (already fetched via useCurrentUser hook)
        if (isLoadingUser) return;
        if (userError || !user) {
          setInitializationError("Failed to load user data. Please try again.");
          setIsInitializing(false);
          return;
        }

        // Step 5: Fetch versions list (already fetched via useResumeVersions hook)
        if (isLoadingVersions) return;
        if (versionsError) {
          console.error("Failed to load versions:", versionsError);
          // Don't block initialization on versions error, continue with empty array
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
          // Initialize empty array if no messages exist
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

        // Step 8: Load draft state from selected version (or initialize empty draft)
        // This will be handled by the existing useEffect that watches selectedVersion

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
        // Format work experience
        const workExperience = await formatWorkExperience();

        // Use analyses from state (already validated during initialization)
        if (!gapAnalysis || !stakeholderAnalysis) {
          toast.error("Analyses not available. Please refresh the page.");
          return;
        }

        // Prepare messages for API (convert to ResumeChatMessage format)
        // Ensure payload matches ResumeChatMessage schema exactly
        const apiMessages: components["schemas"]["ResumeChatMessage"][] =
          chatMessages.map((msg) => ({
            role: msg.role,
            content: msg.content,
            tool_calls: msg.tool_calls || null,
            tool_call_id: msg.tool_call_id || null,
          }));

        // Add user message
        apiMessages.push({
          role: "user",
          content: message,
          tool_calls: null,
          tool_call_id: null,
        });

        // Call resume-chat API with properly typed ResumeChatRequest
        const requestPayload: components["schemas"]["ResumeChatRequest"] = {
          messages: apiMessages,
          job_id: jobId,
          selected_version_id: selectedVersionId || null,
          gap_analysis: gapAnalysis,
          stakeholder_analysis: stakeholderAnalysis,
          work_experience: workExperience,
        };

        const response = await workflowsAPI.resumeChat(requestPayload);

        // Handle response
        const aiMessage = response.message;
        const newVersionId = response.version_id;

        // Convert AI response to chat message format
        const assistantMessage: (typeof chatMessages)[0] = {
          role: "assistant",
          content:
            typeof aiMessage.content === "string" ? aiMessage.content : "",
          tool_calls: Array.isArray(aiMessage.tool_calls)
            ? aiMessage.tool_calls
            : null,
        };

        // Add assistant message to chat
        const updatedMessages = [...chatMessages, assistantMessage];

        // If tool calls were executed, backend returns tool messages
        // We'll add them if they're in the response
        if (aiMessage.tool_calls && Array.isArray(aiMessage.tool_calls)) {
          // Tool messages are handled by backend, but we might need to add them
          // For now, we'll just add the assistant message
        }

        setChatMessages(updatedMessages);

        // Save messages to database
        try {
          await jobsAPI.saveIntakeSessionMessages(
            jobId,
            intakeSession.id,
            2,
            updatedMessages
          );
        } catch (error) {
          console.error("Failed to save messages:", error);
          // Don't show error to user, messages are already in state
        }

        // If new version was created, update selected version
        if (newVersionId) {
          setSelectedVersionId(newVersionId);
          // Refresh versions list by reloading
          window.location.reload();
        }
      } catch (error: unknown) {
        console.error("Failed to send message:", error);
        const err = error as { status?: number; detail?: string };

        // Handle quota errors
        if (err?.status === 429 || err?.detail?.includes("quota")) {
          setQuotaError("API quota exceeded. Please try again later.");
          // Persist error for one render cycle
          setTimeout(() => {
            setQuotaError(null);
          }, 100);
        } else if (err?.status === 422) {
          // Handle validation errors
          toast.error(
            err?.detail || "Validation error. Please check your message."
          );
        } else {
          // Handle network and other errors
          toast.error(
            err?.detail || "Failed to send message. Please try again."
          );
        }
        // Don't remove user message from history on error (per spec)
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

  const handleCopyJobContext = async () => {
    if (!user?.id) {
      toast.error("User information not available");
      return;
    }

    setIsCopyingContext(true);
    try {
      // Fetch all required data
      const [session, userExperiences] = await Promise.all([
        jobsAPI.getIntakeSession(jobId).catch(() => null),
        experiencesAPI.list(user.id),
      ]);

      // Fetch achievements for each experience
      const achievementsByExp = new Map<
        number,
        components["schemas"]["AchievementResponse"][]
      >();
      if (userExperiences) {
        await Promise.all(
          userExperiences.map(async (exp) => {
            try {
              const achievements = await experiencesAPI.listAchievements(
                exp.id
              );
              achievementsByExp.set(exp.id, achievements);
            } catch (error) {
              console.error(
                `Failed to fetch achievements for experience ${exp.id}:`,
                error
              );
            }
          })
        );
      }

      // Format work experience
      const workExperience = userExperiences
        ? formatAllExperiences(userExperiences, achievementsByExp)
        : "No work experience available.";

      // Get job description
      const jobDescription = job?.job_description || "";

      // Get analyses from intake session
      const gapAnalysis = session?.gap_analysis || "";
      const stakeholderAnalysis = session?.stakeholder_analysis || "";

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
        toast.error(
          err?.detail || "Validation error. Please check your data."
        );
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
        toast.error(
          err?.detail || "Validation error. Please check your data."
        );
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
      a.download = `resume_${jobId}_v${
        selectedVersion?.version_index || ""
      }.pdf`;
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
      // Use template name from selected version, or default if no version exists
      const templateName = selectedVersion?.template_name || "resume_000.html";

      // Ensure payload matches ResumeCreate schema exactly
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

      // Update selected version to new version
      if (version.id) {
        setSelectedVersionId(version.id);
      }
      // Reset dirty state by updating loaded version ID
      setLoadedVersionId(version.id || null);

      toast.success("Changes saved as new version!");

      // Trigger PDF preview refresh
      refreshPdfPreview();
    } catch (error: unknown) {
      console.error("Failed to save resume:", error);
      const err = error as { status?: number; detail?: string };
      // Handle validation errors (422)
      if (err?.status === 422) {
        const errorMessage =
          err?.detail || "Validation error. Please check your resume data.";
        toast.error(errorMessage);
      } else {
        toast.error(
          err?.detail || "Failed to save resume. Please try again."
        );
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
      // If no loaded version, reset to empty draft with user's basic info
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
      // Use draft JSON if dirty, otherwise use version JSON
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

      // Clean up old URL
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

  const handleSkip = async () => {
    try {
      // Mark Step 2 as completed
      if (intakeSession) {
        await jobsAPI.updateIntakeSession(jobId, {
          current_step: 3,
          step_completed: 2,
        });
      }
      setCurrentStep("proposals");
      router.push(`/intake/${jobId}/proposals`);
    } catch (error: unknown) {
      console.error("Failed to skip step:", error);
      const err = error as { detail?: string };
      toast.error(err?.detail || "Failed to skip step. Please try again.");
    }
  };

  const handleNext = async () => {
    if (
      !intakeSession ||
      !user?.id ||
      !experiences ||
      experiences.length === 0
    ) {
      toast.error("Missing required data. Please ensure you have experiences.");
      return;
    }

    setIsNextLoading(true);

    try {
      // Prepare chat messages for API (convert to dict format)
      const chatMessagesForAPI = chatMessages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      // Get experience IDs
      const experienceIds = experiences.map((exp) => exp.id);

      // Call experience extraction workflow
      try {
        await workflowsAPI.experienceExtraction({
          chat_messages: chatMessagesForAPI,
          experience_ids: experienceIds,
        });
        // Proposals are created in the database by the workflow
        // Step 3 will fetch them from the API
      } catch (error: unknown) {
        // Handle quota errors gracefully - allow continuing to Step 3 with empty proposals
        const err = error as { status?: number; detail?: string };
        if (err?.status === 429 || err?.detail?.includes("quota")) {
          toast.warning(
            "API quota exceeded. You can continue to review proposals, but some may be missing."
          );
          // Continue to Step 3 even with quota error
        } else {
          // For other errors, show error but still allow continuing
          console.error("Failed to extract experience updates:", error);
          toast.warning(
            err?.detail ||
              "Failed to extract experience updates. You can continue to review proposals."
          );
        }
      }

      // Mark Step 2 as completed
      try {
        await jobsAPI.updateIntakeSession(jobId, {
          current_step: 3,
          step_completed: 2,
        });
      } catch (error: unknown) {
        console.error("Failed to update intake session:", error);
        const err = error as { detail?: string };
        toast.error(
          err?.detail || "Failed to update session. Please try again."
        );
        return;
      }

      // Navigate to Step 3
      setCurrentStep("proposals");
      router.push(`/intake/${jobId}/proposals`);
    } catch (error: unknown) {
      console.error("Failed to proceed to next step:", error);
      const err = error as { detail?: string };
      toast.error(
        err?.detail || "Failed to proceed to next step. Please try again."
      );
    } finally {
      setIsNextLoading(false);
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

  // Ensure we have required data (defensive check)
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

  // Validate analyses exist (defensive check)
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

  // Calculate available height for columns
  // Header height ~60px, action buttons height ~80px, padding ~40px
  const columnHeight = "calc(100vh - 180px)";

  return (
    <div className="flex h-screen flex-col">
      {/* Header Row */}
      <div className="flex items-center justify-between border-b px-6 py-4">
        <h1 className="text-xl font-semibold">
          Job Intake: Step 2 of 3 - Experience & Resume Development
        </h1>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopyJobContext}
          disabled={isCopyingContext}
        >
          <Copy className="mr-2 size-4" />
          {isCopyingContext ? "Copying..." : "Copy job context"}
        </Button>
      </div>

      {/* Two-column grid layout */}
      <div
        className="grid flex-1 gap-4 px-6 py-4 md:grid-cols-[40%_60%]"
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

        {/* Right column: Tabs interface (60%) */}
        <div className="flex flex-col overflow-hidden rounded-lg border">
          <Tabs
            value={selectedTab}
            onValueChange={setSelectedTab}
            className="flex h-full flex-col"
          >
            <div className="border-b px-4 py-2">
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
                  <MarkdownContent content={gapAnalysis || ""} />
                </div>
              </TabsContent>

              <TabsContent value="stakeholder-analysis" className="h-full">
                <div className="h-full overflow-y-auto">
                  <MarkdownContent content={stakeholderAnalysis || ""} />
                </div>
              </TabsContent>

              <TabsContent value="content" className="h-full">
                <div className="space-y-4">
                  {/* Version Navigation */}
                  {versions.length > 0 && (
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

                  {/* Action Buttons Row */}
                  <div className="flex items-center justify-end gap-2">
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
                  </div>

                  {/* Resume Editor */}
                  <div className="overflow-y-auto" style={{ height: "600px" }}>
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
                  {/* Version Navigation */}
                  {versions.length > 0 && (
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

                  {/* PDF Preview */}
                  <div className="h-[600px] overflow-y-auto border rounded-lg p-4 bg-gray-50">
                    {isLoadingPdf && (
                      <div className="flex h-full items-center justify-center">
                        <div className="text-muted-foreground">
                          Loading PDF preview...
                        </div>
                      </div>
                    )}
                    {pdfError && (
                      <div className="flex h-full items-center justify-center">
                        <Alert>
                          <AlertDescription>{pdfError}</AlertDescription>
                        </Alert>
                      </div>
                    )}
                    {!isLoadingPdf &&
                      !pdfError &&
                      !pdfPreviewUrl &&
                      versions.length === 0 && (
                        <div className="flex h-full items-center justify-center">
                          <Alert>
                            <AlertDescription>
                              No resume version available yet. Use the chat or
                              edit the Resume Content tab to create one.
                            </AlertDescription>
                          </Alert>
                        </div>
                      )}
                    {!isLoadingPdf && !pdfError && pdfPreviewUrl && (
                      <div className="flex justify-center">
                        <Document
                          file={pdfPreviewUrl}
                          loading={
                            <div className="flex items-center justify-center p-4">
                              <div className="text-muted-foreground">
                                Loading PDF...
                              </div>
                            </div>
                          }
                          error={
                            <Alert>
                              <AlertDescription>
                                Failed to render PDF preview
                              </AlertDescription>
                            </Alert>
                          }
                        >
                          <Page
                            pageNumber={1}
                            width={600}
                            renderTextLayer={true}
                            renderAnnotationLayer={true}
                          />
                        </Document>
                      </div>
                    )}
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>
      </div>

      {/* Bottom action buttons row */}
      <div className="flex items-center justify-between border-t px-6 py-4">
        <Button
          variant="outline"
          onClick={handleBack}
          disabled={isNextLoading || isChatLoading}
        >
          Back
        </Button>
        <div className="flex gap-4">
          <Button
            variant="outline"
            onClick={handleSkip}
            disabled={isNextLoading || isChatLoading}
          >
            Skip
          </Button>
          <Button
            onClick={handleNext}
            disabled={!canonicalVersionId || isNextLoading || isChatLoading}
          >
            {isNextLoading ? "Processing..." : "Next"}
          </Button>
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
