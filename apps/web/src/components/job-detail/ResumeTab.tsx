"use client";

import { useState, useEffect, useMemo, useCallback, useRef } from "react";
import { Download, Pin, Sparkles, ChevronLeft, ChevronRight, Copy } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { useCurrentUser } from "@/lib/hooks/useUser";
import {
  useCreateResumeVersion,
  useCurrentResume,
  useGenerateResume,
  usePinResumeVersion,
  useResumeVersion,
  useResumeVersions,
} from "@/lib/hooks/useResumes";
import { resumesAPI } from "@/lib/api/resumes";
import { templatesAPI } from "@/lib/api/templates";
import { workflowsAPI } from "@/lib/api/workflows";
import { ResumeEditor } from "@/components/resume/ResumeEditor";
import type { components } from "@/types/api";

type ResumeVersionResponse = components["schemas"]["ResumeVersionResponse"];
type ResumeData = components["schemas"]["ResumeData"];
type JobStatus = components["schemas"]["JobStatus"];

interface ResumeTabProps {
  jobId: number;
  jobDescription?: string;
  jobStatus: JobStatus;
}

export function ResumeTab({ jobId, jobDescription = "", jobStatus }: ResumeTabProps) {
  const { data: user } = useCurrentUser();
  const isReadOnly = jobStatus === "Applied";

  // State
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const [instructions, setInstructions] = useState("");
  const [templateName, setTemplateName] = useState("resume_000.html");
  const [draftResume, setDraftResume] = useState<ResumeData | null>(null);
  const [lastSavedResume, setLastSavedResume] = useState<ResumeData | null>(null);
  const [lastSavedTemplate, setLastSavedTemplate] = useState<string>("resume_000.html");
  const [showUnsavedDialog, setShowUnsavedDialog] = useState(false);
  const [pendingNavigation, setPendingNavigation] = useState<(() => void) | null>(null);
  const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);

  // Fetch data
  const { data: versions, isLoading: isLoadingVersions } = useResumeVersions(jobId);
  const { data: currentResume, isLoading: isLoadingCurrent } = useCurrentResume(jobId);
  const { data: selectedVersion, isLoading: isLoadingSelected } = useResumeVersion(
    jobId,
    selectedVersionId ?? 0
  );

  // Fetch templates
  const { data: templatesData } = useQuery({
    queryKey: ["templates", "resumes"],
    queryFn: () => templatesAPI.listResumeTemplates(),
  });

  const templates = templatesData?.templates || [];
  const templateOptions = templates.map((t) => t.name);

  // Mutations
  const createVersion = useCreateResumeVersion();
  const pinVersion = usePinResumeVersion();
  const generateResume = useGenerateResume();

  // Determine which resume to display
  const displayVersion = selectedVersionId ? selectedVersion : null;
  const displayResumeJson = displayVersion
    ? displayVersion.resume_json
    : currentResume?.resume_json || null;

  const baseResumeData: ResumeData | null = useMemo(() => {
    return displayResumeJson ? (JSON.parse(displayResumeJson) as ResumeData) : null;
  }, [displayResumeJson]);

  // Determine canonical version
  const canonicalVersionId = useMemo(() => {
    if (!versions || !currentResume) return null;
    for (const version of versions) {
      if (version.resume_json === currentResume.resume_json) {
        return version.id || null;
      }
    }
    return null;
  }, [versions, currentResume]);

  // Current version index
  const currentVersionIndex = selectedVersionId
    ? versions?.find((v) => v.id === selectedVersionId)?.version_index || 0
    : canonicalVersionId
      ? versions?.find((v) => v.id === canonicalVersionId)?.version_index || 0
      : versions?.[versions.length - 1]?.version_index || 0;

  // Version navigation
  const canGoPrevious = currentVersionIndex > 1;
  const canGoNext = currentVersionIndex < (versions?.length || 0);

  // Dirty state
  const isDirty = useMemo(() => {
    if (!draftResume || !lastSavedResume) return false;
    return (
      JSON.stringify(draftResume) !== JSON.stringify(lastSavedResume) ||
      templateName !== lastSavedTemplate
    );
  }, [draftResume, lastSavedResume, templateName, lastSavedTemplate]);

  // Validation
  const validationErrors = useMemo(() => {
    const errors: string[] = [];
    if (!draftResume?.name || draftResume.name.trim() === "") {
      errors.push("Name is required");
    }
    if (!draftResume?.email || draftResume.email.trim() === "") {
      errors.push("Email is required");
    }
    if (!draftResume?.experience || draftResume.experience.length === 0) {
      errors.push("At least one experience is required");
    }
    return errors;
  }, [draftResume]);

  // Store PDF preview URL ref for cleanup
  const pdfPreviewUrlRef = useRef<string | null>(null);

  // Refresh PDF preview - only called after save/generate
  const refreshPdfPreview = useCallback(async () => {
    if (!draftResume || validationErrors.length > 0) {
      if (pdfPreviewUrlRef.current) {
        URL.revokeObjectURL(pdfPreviewUrlRef.current);
        pdfPreviewUrlRef.current = null;
      }
      setPdfPreviewUrl(null);
      return;
    }

    try {
      // Clean up old URL
      if (pdfPreviewUrlRef.current) {
        URL.revokeObjectURL(pdfPreviewUrlRef.current);
      }

      const blob = await resumesAPI.previewPDFDraft(jobId, {
        resume_data: draftResume,
        template_name: templateName,
      });
      const url = URL.createObjectURL(blob);
      pdfPreviewUrlRef.current = url;
      setPdfPreviewUrl(url);
    } catch (error) {
      console.error("Failed to preview PDF:", error);
      setPdfPreviewUrl(null);
    }
  }, [draftResume, templateName, jobId, validationErrors.length]);

  // Initialize draft from base resume
  useEffect(() => {
    if (baseResumeData) {
      // Reset draft when version changes
      setDraftResume(baseResumeData);
      setLastSavedResume(baseResumeData);
      if (displayVersion) {
        setLastSavedTemplate(displayVersion.template_name);
        setTemplateName(displayVersion.template_name);
      } else if (currentResume && versions) {
        // Use template from pinned version if available
        const pinnedVersion = versions.find((v) => v.id === canonicalVersionId);
        const currentTemplate = pinnedVersion?.template_name || "resume_000.html";
        setLastSavedTemplate(currentTemplate);
        setTemplateName(currentTemplate);
      }
    }
  }, [baseResumeData, displayVersion, currentResume, versions, canonicalVersionId]);

  const canGenerate = !isReadOnly && validationErrors.length === 0 && user;
  const canSave = !isReadOnly && isDirty && validationErrors.length === 0;
  const canDownload = !isDirty && canonicalVersionId !== null && !isReadOnly;

  // Handle version navigation with unsaved changes check
  const handleVersionNavigation = useCallback(
    (newVersionId: number | null) => {
      if (isDirty) {
        setPendingNavigation(() => () => {
          setSelectedVersionId(newVersionId);
          setDraftResume(null);
          setLastSavedResume(null);
          setShowUnsavedDialog(false);
          setPendingNavigation(null);
          // Refresh PDF preview after navigation
          setTimeout(() => refreshPdfPreview(), 100);
        });
        setShowUnsavedDialog(true);
      } else {
        setSelectedVersionId(newVersionId);
        setDraftResume(null);
        setLastSavedResume(null);
        // Refresh PDF preview after navigation
        setTimeout(() => refreshPdfPreview(), 100);
      }
    },
    [isDirty, refreshPdfPreview]
  );

  const handlePreviousVersion = () => {
    if (!canGoPrevious) return;
    const prevVersion = versions?.find((v) => v.version_index === currentVersionIndex - 1);
    if (prevVersion?.id) {
      handleVersionNavigation(prevVersion.id);
    }
  };

  const handleNextVersion = () => {
    if (!canGoNext) return;
    const nextVersion = versions?.find((v) => v.version_index === currentVersionIndex + 1);
    if (nextVersion?.id) {
      handleVersionNavigation(nextVersion.id);
    }
  };

  const handleVersionSelect = (value: string) => {
    if (value === "current") {
      handleVersionNavigation(null);
    } else {
      const versionId = parseInt(value, 10);
      handleVersionNavigation(versionId);
    }
  };

  // Save changes
  const handleSave = async () => {
    if (!draftResume || !user) return;

    try {
      const version = await createVersion.mutateAsync({
        jobId,
        data: {
          resume_json: JSON.stringify(draftResume),
          template_name: templateName,
          event_type: "save",
          parent_version_id: displayVersion?.id || null,
        },
      });

      setLastSavedResume(draftResume);
      setLastSavedTemplate(templateName);
      setSelectedVersionId(version.id || null);

      // Refresh PDF preview
      await refreshPdfPreview();

      toast.success("Resume saved", {
        description: "Your changes have been saved successfully.",
      });
    } catch (error) {
      console.error("Failed to save resume:", error);
      toast.error("Failed to save", {
        description: "There was an error saving your resume. Please try again.",
      });
    }
  };

  // Discard changes
  const handleDiscard = () => {
    if (lastSavedResume) {
      setDraftResume(lastSavedResume);
    } else if (baseResumeData) {
      setDraftResume(baseResumeData);
    }
    setTemplateName(lastSavedTemplate);
  };

  // Generate resume
  const handleGenerate = async () => {
    if (!user || !draftResume) return;

    try {
      const response = await generateResume.mutateAsync({
        userId: user.id,
        request: {
          job_description: jobDescription,
          experiences: [],
          responses: "",
          resume_draft: draftResume,
        },
      });

      // Update draft with generated data
      setDraftResume(response.resume_data);

      // Create version
      const version = await createVersion.mutateAsync({
        jobId,
        data: {
          resume_json: JSON.stringify(response.resume_data),
          template_name: templateName,
          event_type: "generate",
          parent_version_id: displayVersion?.id || null,
        },
      });

      setSelectedVersionId(version.id || null);
      setLastSavedResume(response.resume_data);
      setLastSavedTemplate(templateName);

      // Refresh PDF preview
      await refreshPdfPreview();

      toast.success("Resume generated", {
        description: "Your resume has been generated successfully.",
      });
    } catch (error) {
      console.error("Failed to generate resume:", error);
      toast.error("Failed to generate", {
        description: "There was an error generating your resume. Please try again.",
      });
    }
  };

  // Pin version
  const handlePinVersion = async () => {
    if (!selectedVersionId) return;

    try {
      await pinVersion.mutateAsync({ jobId, versionId: selectedVersionId });
      setSelectedVersionId(null);
      toast.success("Version pinned", {
        description: "This version is now the canonical resume.",
      });
    } catch (error) {
      console.error("Failed to pin version:", error);
      toast.error("Failed to pin", {
        description: "There was an error pinning this version.",
      });
    }
  };

  // Download PDF
  const handleDownloadPDF = async () => {
    if (!canonicalVersionId) return;

    try {
      const blob = await resumesAPI.downloadPDF(jobId, canonicalVersionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume_${jobId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download PDF:", error);
      toast.error("Failed to download", {
        description: "There was an error downloading the PDF.",
      });
    }
  };

  // Copy resume text
  const handleCopyResume = () => {
    if (!draftResume) return;

    const text = formatResumeAsText(draftResume);
    navigator.clipboard.writeText(text);
    toast.success("Copied", {
      description: "Resume text copied to clipboard.",
    });
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pdfPreviewUrlRef.current) {
        URL.revokeObjectURL(pdfPreviewUrlRef.current);
      }
    };
  }, []);

  // Update draft resume
  const updateDraftResume = (updater: (prev: ResumeData) => ResumeData) => {
    setDraftResume((prev) => (prev ? updater(prev) : null));
  };

  const isLoading = isLoadingVersions || isLoadingCurrent || isLoadingSelected;

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="text-muted-foreground">Loading resume...</div>
      </div>
    );
  }

  if (!draftResume && !baseResumeData) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center gap-4">
        <p className="text-lg text-muted-foreground">No resume data available</p>
        {!isReadOnly && (
          <Button onClick={handleGenerate} disabled={generateResume.isPending || !user}>
            <Sparkles className="mr-2 size-4" />
            Generate Your First Resume
          </Button>
        )}
      </div>
    );
  }

  const resumeData = draftResume || baseResumeData!;

  return (
    <div className="space-y-4">
      {/* Two-column layout */}
      <div className="grid grid-cols-[60%_40%] gap-6">
        {/* Left Column - Content Editor */}
        <div className="space-y-4">
          {/* Instructions */}
          {!isReadOnly && (
            <div>
              <Label htmlFor="instructions">What should the AI change?</Label>
              <Textarea
                id="instructions"
                value={instructions}
                onChange={(e) => setInstructions(e.target.value)}
                placeholder="Enter instructions for AI generation..."
                className="mt-2 min-h-[300px]"
                disabled={isReadOnly}
              />
            </div>
          )}

          {/* Control Row */}
          {!isReadOnly && (
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Button
                  onClick={handleGenerate}
                  disabled={!canGenerate || generateResume.isPending || createVersion.isPending}
                >
                  <Sparkles className="mr-2 size-4" />
                  Generate
                </Button>
                <Button onClick={handleSave} disabled={!canSave || createVersion.isPending}>
                  Save
                </Button>
                <Button
                  variant="outline"
                  onClick={handleDiscard}
                  disabled={!isDirty}
                >
                  Discard
                </Button>
              </div>
              <Select value={templateName} onValueChange={setTemplateName} disabled={isReadOnly}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {templateOptions.map((name) => (
                    <SelectItem key={name} value={name}>
                      {name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Version Navigation */}
          {!isReadOnly && versions && versions.length > 0 && (
            <div className="flex items-center gap-2 border rounded-lg p-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handlePreviousVersion}
                disabled={!canGoPrevious}
              >
                <ChevronLeft className="size-4" />
              </Button>
              <Select
                value={selectedVersionId?.toString() || "current"}
                onValueChange={handleVersionSelect}
              >
                <SelectTrigger className="w-[150px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="current">
                    v{currentVersionIndex} {canonicalVersionId === null ? "(pinned)" : ""}
                  </SelectItem>
                  {versions.map((version) => (
                    <SelectItem key={version.id} value={version.id?.toString() || ""}>
                      v{version.version_index} {version.id === canonicalVersionId ? "(pinned)" : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleNextVersion}
                disabled={!canGoNext}
              >
                <ChevronRight className="size-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handlePinVersion}
                disabled={!selectedVersionId || selectedVersionId === canonicalVersionId}
              >
                <Pin className={`size-4 ${selectedVersionId === canonicalVersionId ? "fill-current" : ""}`} />
              </Button>
            </div>
          )}

          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <div className="text-sm text-destructive">
                  <p className="font-semibold mb-2">Missing required fields:</p>
                  <ul className="list-disc list-inside space-y-1">
                    {validationErrors.map((error, idx) => (
                      <li key={idx}>{error}</li>
                    ))}
                  </ul>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Content Tabs */}
          <ResumeEditor
            resumeData={resumeData}
            updateResume={updateDraftResume}
            readOnly={isReadOnly}
          />
        </div>

        {/* Right Column - Preview */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Preview</h3>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleCopyResume}>
                <Copy className="mr-2 size-4" />
                Copy
              </Button>
              <Button
                size="sm"
                onClick={handleDownloadPDF}
                disabled={!canDownload}
              >
                <Download className="mr-2 size-4" />
                Download
              </Button>
            </div>
          </div>

          {validationErrors.length > 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">
                  Please fill in required fields (name, email, at least one experience) to see preview.
                </p>
              </CardContent>
            </Card>
          ) : pdfPreviewUrl ? (
            <iframe
              src={pdfPreviewUrl}
              className="w-full h-[800px] border rounded-lg"
              title="Resume Preview"
            />
          ) : (
            <Card>
              <CardContent className="pt-6">
                <p className="text-sm text-muted-foreground">Preview will appear after save or generate.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Unsaved Changes Dialog */}
      <Dialog open={showUnsavedDialog} onOpenChange={setShowUnsavedDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Unsaved Changes</DialogTitle>
            <DialogDescription>
              You have unsaved changes. What would you like to do?
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowUnsavedDialog(false);
                setPendingNavigation(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                handleDiscard();
                if (pendingNavigation) {
                  pendingNavigation();
                }
              }}
            >
              Discard Changes
            </Button>
            <Button
              onClick={async () => {
                await handleSave();
                if (pendingNavigation) {
                  pendingNavigation();
                }
              }}
            >
              Save & Continue
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
