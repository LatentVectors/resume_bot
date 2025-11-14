"use client";

import { useState } from "react";
import { Download, Pin, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import type { components } from "@/types/api";

type ResumeVersionResponse = components["schemas"]["ResumeVersionResponse"];
type ResumeData = components["schemas"]["ResumeData"];

interface ResumeTabProps {
  jobId: number;
  jobDescription?: string;
}

export function ResumeTab({ jobId, jobDescription = "" }: ResumeTabProps) {
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(null);
  const { data: user } = useCurrentUser();

  // Fetch resume data
  const { data: versions, isLoading: isLoadingVersions } = useResumeVersions(jobId);
  const { data: currentResume, isLoading: isLoadingCurrent } = useCurrentResume(jobId);
  const { data: selectedVersion, isLoading: isLoadingSelected } = useResumeVersion(
    jobId,
    selectedVersionId ?? 0
  );

  // Mutations
  const createVersion = useCreateResumeVersion();
  const pinVersion = usePinResumeVersion();
  const generateResume = useGenerateResume();

  // Determine which resume to display
  const displayVersion = selectedVersionId ? selectedVersion : null;
  const displayResumeJson = displayVersion
    ? displayVersion.resume_json
    : currentResume?.resume_json || null;

  const displayResumeData: ResumeData | null = displayResumeJson
    ? (JSON.parse(displayResumeJson) as ResumeData)
    : null;

  const handleGenerateResume = async () => {
    if (!user || !currentResume) return;

    try {
      // Generate resume using workflow
      const response = await generateResume.mutateAsync({
        userId: user.id,
        request: {
          job_description: jobDescription,
          resume_draft: displayResumeData || null,
        },
      });

      // Create a new version with the generated resume
      await createVersion.mutateAsync({
        jobId,
        data: {
          resume_json: JSON.stringify(response.resume_data),
          template_name: "resume_000.html", // Default template
          event_type: "generate",
          parent_version_id: displayVersion?.id || null,
        },
      });
    } catch (error) {
      console.error("Failed to generate resume:", error);
    }
  };

  const handlePinVersion = async (versionId: number) => {
    try {
      await pinVersion.mutateAsync({ jobId, versionId });
      setSelectedVersionId(null); // Reset selection to show pinned version
    } catch (error) {
      console.error("Failed to pin version:", error);
    }
  };

  const handleDownloadPDF = async (versionId: number) => {
    try {
      const blob = await resumesAPI.downloadPDF(jobId, versionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `resume_${jobId}_v${versionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download PDF:", error);
    }
  };

  const isLoading = isLoadingVersions || isLoadingCurrent || isLoadingSelected;

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Resume</h2>
          <p className="text-muted-foreground">
            Manage resume versions and generate new ones
          </p>
        </div>
        <div className="flex items-center gap-2">
          {versions && versions.length > 0 && (
            <Select
              value={selectedVersionId?.toString() || "current"}
              onValueChange={(value) =>
                setSelectedVersionId(value === "current" ? null : parseInt(value, 10))
              }
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select version" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="current">
                  Current (Pinned)
                </SelectItem>
                {versions.map((version) => (
                  <SelectItem key={version.id} value={version.id.toString()}>
                    Version {version.version_index}
                    {version.is_pinned && " (Pinned)"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button
            onClick={handleGenerateResume}
            disabled={generateResume.isPending || createVersion.isPending || !user}
          >
            <Sparkles className="mr-2 size-4" />
            {generateResume.isPending || createVersion.isPending
              ? "Generating..."
              : "Generate Resume"}
          </Button>
        </div>
      </div>

      {/* Versions List */}
      {isLoading ? (
        <Card>
          <CardContent className="flex min-h-[400px] items-center justify-center">
            <div className="text-muted-foreground">Loading resume...</div>
          </CardContent>
        </Card>
      ) : !versions || versions.length === 0 ? (
        <Card>
          <CardContent className="flex min-h-[400px] flex-col items-center justify-center gap-4">
            <p className="text-lg text-muted-foreground">No resume versions yet</p>
            <Button onClick={handleGenerateResume} disabled={generateResume.isPending || !user}>
              <Sparkles className="mr-2 size-4" />
              Generate Your First Resume
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Versions List Card */}
          <Card>
            <CardHeader>
              <CardTitle>Resume Versions</CardTitle>
              <CardDescription>Select a version to view or pin</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {versions.map((version) => (
                  <VersionItem
                    key={version.id}
                    version={version}
                    isSelected={selectedVersionId === version.id}
                    onSelect={() => setSelectedVersionId(version.id)}
                    onPin={() => handlePinVersion(version.id)}
                    onDownload={() => handleDownloadPDF(version.id)}
                  />
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Resume Content */}
          {displayResumeData ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Resume Content</CardTitle>
                    <CardDescription>
                      {selectedVersionId
                        ? `Version ${selectedVersion?.version_index || "N/A"}`
                        : "Current Resume"}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {selectedVersionId && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handlePinVersion(selectedVersionId)}
                        disabled={pinVersion.isPending}
                      >
                        <Pin className="mr-2 size-4" />
                        Pin Version
                      </Button>
                    )}
                    {(displayVersion || currentResume) && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() =>
                          handleDownloadPDF(
                            selectedVersionId || versions?.[0]?.id || 0
                          )
                        }
                      >
                        <Download className="mr-2 size-4" />
                        Download PDF
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <ResumeContentDisplay resumeData={displayResumeData} />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex min-h-[400px] items-center justify-center">
                <div className="text-muted-foreground">No resume content available</div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

interface VersionItemProps {
  version: ResumeVersionResponse;
  isSelected: boolean;
  onSelect: () => void;
  onPin: () => void;
  onDownload: () => void;
}

function VersionItem({
  version,
  isSelected,
  onSelect,
  onPin,
  onDownload,
}: VersionItemProps) {
  return (
    <div
      className={`flex items-center justify-between rounded-lg border p-3 transition-colors ${
        isSelected ? "border-primary bg-muted" : "border-border hover:bg-muted/50"
      }`}
    >
      <div className="flex items-center gap-3">
        <button
          onClick={onSelect}
          className="flex-1 text-left"
        >
          <div className="flex items-center gap-2">
            <span className="font-medium">Version {version.version_index}</span>
            {version.event_type && (
              <Badge variant="outline">{version.event_type}</Badge>
            )}
          </div>
          <div className="text-sm text-muted-foreground">
            Created {new Date(version.created_at).toLocaleDateString()}
          </div>
        </button>
      </div>
      <div className="flex items-center gap-2">
        <Button variant="ghost" size="sm" onClick={onPin}>
          <Pin className="size-4" />
        </Button>
        <Button variant="ghost" size="sm" onClick={onDownload}>
          <Download className="size-4" />
        </Button>
      </div>
    </div>
  );
}

interface ResumeContentDisplayProps {
  resumeData: ResumeData;
}

function ResumeContentDisplay({ resumeData }: ResumeContentDisplayProps) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b pb-4">
        <h3 className="text-xl font-bold">{resumeData.name}</h3>
        <p className="text-muted-foreground">{resumeData.title}</p>
        <div className="mt-2 flex flex-wrap gap-4 text-sm">
          {resumeData.email && <span>{resumeData.email}</span>}
          {resumeData.phone && <span>{resumeData.phone}</span>}
          {resumeData.linkedin_url && (
            <a
              href={resumeData.linkedin_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              LinkedIn
            </a>
          )}
        </div>
      </div>

      {/* Professional Summary */}
      {resumeData.professional_summary && (
        <div>
          <h4 className="mb-2 font-semibold">Professional Summary</h4>
          <p className="text-muted-foreground whitespace-pre-wrap">
            {resumeData.professional_summary}
          </p>
        </div>
      )}

      {/* Experience */}
      {resumeData.experience && resumeData.experience.length > 0 && (
        <div>
          <h4 className="mb-2 font-semibold">Experience</h4>
          <div className="space-y-4">
            {resumeData.experience.map((exp, idx) => (
              <div key={idx} className="border-l-2 border-primary pl-4">
                <div className="font-medium">{exp.title}</div>
                <div className="text-sm text-muted-foreground">
                  {exp.company} • {exp.start_date} - {exp.end_date || "Present"}
                </div>
                {exp.description && (
                  <p className="mt-2 text-sm whitespace-pre-wrap">{exp.description}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Education */}
      {resumeData.education && resumeData.education.length > 0 && (
        <div>
          <h4 className="mb-2 font-semibold">Education</h4>
          <div className="space-y-2">
            {resumeData.education.map((edu, idx) => (
              <div key={idx}>
                <div className="font-medium">{edu.degree} in {edu.major}</div>
                <div className="text-sm text-muted-foreground">
                  {edu.institution} • {edu.graduation_date}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Skills */}
      {resumeData.skills && resumeData.skills.length > 0 && (
        <div>
          <h4 className="mb-2 font-semibold">Skills</h4>
          <div className="flex flex-wrap gap-2">
            {resumeData.skills.map((skill, idx) => (
              <Badge key={idx} variant="secondary">
                {skill}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Certifications */}
      {resumeData.certifications && resumeData.certifications.length > 0 && (
        <div>
          <h4 className="mb-2 font-semibold">Certifications</h4>
          <div className="space-y-2">
            {resumeData.certifications.map((cert, idx) => (
              <div key={idx}>
                <div className="font-medium">{cert.name}</div>
                {cert.issuer && (
                  <div className="text-sm text-muted-foreground">{cert.issuer}</div>
                )}
                {cert.date && (
                  <div className="text-sm text-muted-foreground">{cert.date}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

