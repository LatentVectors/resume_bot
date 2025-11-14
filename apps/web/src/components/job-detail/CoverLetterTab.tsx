"use client";

import { useState } from "react";
import { Download, Pin, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useCreateCoverLetterVersion,
  useCurrentCoverLetter,
  useCoverLetterVersions,
  useCoverLetterVersion,
  usePinCoverLetterVersion,
} from "@/lib/hooks/useCoverLetters";
import { coverLettersAPI } from "@/lib/api/cover-letters";
import type { components } from "@/types/api";

type CoverLetterVersionResponse =
  components["schemas"]["CoverLetterVersionResponse"];
// CoverLetterData is parsed from cover_letter_json string
type CoverLetterData = {
  name: string;
  title?: string;
  email: string;
  phone?: string;
  linkedin_url?: string;
  date?: string;
  company?: string;
  job_title?: string;
  body_paragraphs: string[];
};

interface CoverLetterTabProps {
  jobId: number;
}

export function CoverLetterTab({ jobId }: CoverLetterTabProps) {
  const [selectedVersionId, setSelectedVersionId] = useState<number | null>(
    null
  );

  // Fetch cover letter data
  const { data: versions, isLoading: isLoadingVersions } =
    useCoverLetterVersions(jobId);
  const { data: currentCoverLetter, isLoading: isLoadingCurrent } =
    useCurrentCoverLetter(jobId);
  const { data: selectedVersion } = useCoverLetterVersion(
    jobId,
    selectedVersionId ?? 0
  );

  // Mutations
  const pinVersion = usePinCoverLetterVersion();

  // Determine which cover letter to display
  const displayVersion = selectedVersionId ? selectedVersion : null;
  const displayCoverLetterJson = displayVersion
    ? displayVersion.cover_letter_json
    : currentCoverLetter?.cover_letter_json || null;

  const displayCoverLetterData: CoverLetterData | null = displayCoverLetterJson
    ? (JSON.parse(displayCoverLetterJson) as CoverLetterData)
    : null;

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
      const blob = await coverLettersAPI.downloadPDF(jobId, versionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cover_letter_${jobId}_v${versionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Failed to download PDF:", error);
    }
  };

  const isLoading = isLoadingVersions || isLoadingCurrent;

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Cover Letter</h2>
          <p className="text-muted-foreground">Manage cover letter versions</p>
        </div>
        <div className="flex items-center gap-2">
          {versions && versions.length > 0 && (
            <Select
              value={selectedVersionId?.toString() || "current"}
              onValueChange={(value) =>
                setSelectedVersionId(
                  value === "current" ? null : parseInt(value, 10)
                )
              }
            >
              <SelectTrigger className="w-[200px]">
                <SelectValue placeholder="Select version" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="current">Current</SelectItem>
                {versions.map((version) => (
                  <SelectItem key={version.id} value={version.id.toString()}>
                    Version {version.version_index}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          <Button variant="outline" disabled>
            <FileText className="mr-2 size-4" />
            Generate Cover Letter
          </Button>
        </div>
      </div>

      {/* Versions List */}
      {isLoading ? (
        <Card>
          <CardContent className="flex min-h-[400px] items-center justify-center">
            <div className="text-muted-foreground">Loading cover letter...</div>
          </CardContent>
        </Card>
      ) : !versions || versions.length === 0 ? (
        <Card>
          <CardContent className="flex min-h-[400px] flex-col items-center justify-center gap-4">
            <p className="text-lg text-muted-foreground">
              No cover letter versions yet
            </p>
            <Button variant="outline" disabled>
              <FileText className="mr-2 size-4" />
              Generate Your First Cover Letter
            </Button>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Versions List Card */}
          <Card>
            <CardHeader>
              <CardTitle>Cover Letter Versions</CardTitle>
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

          {/* Cover Letter Content */}
          {displayCoverLetterData ? (
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Cover Letter Content</CardTitle>
                    <CardDescription>
                      {selectedVersionId
                        ? `Version ${selectedVersion?.version_index || "N/A"}`
                        : "Current Cover Letter"}
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
                    {(displayVersion || currentCoverLetter) && (
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
                <CoverLetterContentDisplay
                  coverLetterData={displayCoverLetterData}
                />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex min-h-[400px] items-center justify-center">
                <div className="text-muted-foreground">
                  No cover letter content available
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}

interface VersionItemProps {
  version: CoverLetterVersionResponse;
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
        isSelected
          ? "border-primary bg-muted"
          : "border-border hover:bg-muted/50"
      }`}
    >
      <div className="flex items-center gap-3">
        <button onClick={onSelect} className="flex-1 text-left">
          <div className="flex items-center gap-2">
            <span className="font-medium">Version {version.version_index}</span>
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

interface CoverLetterContentDisplayProps {
  coverLetterData: CoverLetterData;
}

function CoverLetterContentDisplay({
  coverLetterData,
}: CoverLetterContentDisplayProps) {
  return (
    <div className="space-y-6">
      {/* Sender Info */}
      <div className="border-b pb-4">
        <div className="font-semibold text-lg">{coverLetterData.name}</div>
        {coverLetterData.title && (
          <div className="text-muted-foreground">{coverLetterData.title}</div>
        )}
        <div className="mt-2 flex flex-wrap gap-4 text-sm">
          {coverLetterData.email && <span>{coverLetterData.email}</span>}
          {coverLetterData.phone && <span>{coverLetterData.phone}</span>}
        </div>
        {coverLetterData.date && (
          <div className="mt-4 text-sm text-muted-foreground">
            {new Date(coverLetterData.date).toLocaleDateString("en-US", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </div>
        )}
      </div>

      {/* Salutation */}
      <div>Dear Hiring Manager,</div>

      {/* Body Paragraphs */}
      {coverLetterData.body_paragraphs &&
        coverLetterData.body_paragraphs.length > 0 && (
          <div className="space-y-4">
            {coverLetterData.body_paragraphs.map((paragraph, idx) => (
              <p key={idx} className="whitespace-pre-wrap">
                {paragraph}
              </p>
            ))}
          </div>
        )}

      {/* Closing */}
      <div className="mt-8 space-y-2">
        <div>Sincerely,</div>
        <div className="mt-8">{coverLetterData.name}</div>
      </div>
    </div>
  );
}
