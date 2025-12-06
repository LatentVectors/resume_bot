"use client";

import {
  ChevronLeft,
  ChevronRight,
  Pin,
  Copy,
  Download,
  MoreVertical,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";
import type { ResumeVersion } from "@resume/database/types";

interface VersionNavigationProps {
  versions: ResumeVersion[];
  selectedVersionId: number | null;
  canonicalVersionId: number | null;
  onVersionChange: (versionId: number | null) => void;
  onPin: (versionId: number) => void;
  onUnpin: () => void;
  className?: string;
  disabled?: boolean;
}

export function VersionNavigation({
  versions,
  selectedVersionId,
  canonicalVersionId,
  onVersionChange,
  onPin,
  onUnpin,
  className,
  disabled = false,
}: VersionNavigationProps) {
  if (!versions || versions.length === 0) {
    return null;
  }

  const sortedVersions = [...versions].sort((a, b) => {
    const indexA = a.version_index || 0;
    const indexB = b.version_index || 0;
    return indexB - indexA;
  });

  const currentVersion = sortedVersions.find((v) => v.id === selectedVersionId);
  const currentVersionIndex = currentVersion?.version_index || 0;
  const oldestVersion = sortedVersions[sortedVersions.length - 1];
  const latestVersion = sortedVersions[0];
  const oldestVersionIndex = oldestVersion?.version_index || 1;
  const latestVersionIndex = latestVersion?.version_index || 1;

  const isPinned = selectedVersionId === canonicalVersionId;
  const canGoPrevious = currentVersionIndex > oldestVersionIndex;
  const canGoNext = currentVersionIndex < latestVersionIndex;

  const containerClass = cn("flex items-center gap-2", className);
  const navDisabled = disabled;

  const handlePrevious = () => {
    if (navDisabled) return;
    const currentIdx = sortedVersions.findIndex((v) => v.id === selectedVersionId);
    if (currentIdx < sortedVersions.length - 1) {
      const prevVersion = sortedVersions[currentIdx + 1];
      if (prevVersion?.id) {
        onVersionChange(prevVersion.id);
      }
    }
  };

  const handleNext = () => {
    if (navDisabled) return;
    const currentIdx = sortedVersions.findIndex((v) => v.id === selectedVersionId);
    if (currentIdx > 0) {
      const nextVersion = sortedVersions[currentIdx - 1];
      if (nextVersion?.id) {
        onVersionChange(nextVersion.id);
      }
    }
  };

  const handleVersionSelect = (value: string) => {
    if (navDisabled) return;
    if (value === "null" || value === "") {
      onVersionChange(null);
    } else {
      const versionId = parseInt(value, 10);
      if (!isNaN(versionId)) {
        onVersionChange(versionId);
      }
    }
  };

  const handlePinClick = () => {
    if (navDisabled) return;
    if (isPinned) {
      onUnpin();
    } else if (selectedVersionId) {
      onPin(selectedVersionId);
    }
  };

  return (
    <div className={containerClass}>
      <Button
        variant="ghost"
        size="sm"
        onClick={handlePrevious}
        disabled={navDisabled || !canGoPrevious}
      >
        <ChevronLeft className="size-4" />
      </Button>

      <Select
        value={selectedVersionId?.toString() || "null"}
        onValueChange={handleVersionSelect}
        disabled={navDisabled}
      >
        <SelectTrigger className="w-[150px]">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {sortedVersions.map((version) => (
            <SelectItem key={version.id} value={version.id?.toString() || ""}>
              v{version.version_index}
              {version.id === canonicalVersionId ? " (pinned)" : ""}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Button
        variant="ghost"
        size="sm"
        onClick={handleNext}
        disabled={navDisabled || !canGoNext}
      >
        <ChevronRight className="size-4" />
      </Button>

      <Button
        variant={isPinned ? "default" : "outline"}
        size="sm"
        onClick={handlePinClick}
        disabled={navDisabled || !selectedVersionId}
      >
        <Pin className={`size-4 ${isPinned ? "fill-current" : ""}`} />
      </Button>
    </div>
  );
}

interface VersionActionMenuProps {
  disabled?: boolean;
  isPinned: boolean;
  onCopyResume: () => void;
  onDownloadResume: () => void;
}

export function VersionActionMenu({
  disabled = false,
  isPinned,
  onCopyResume,
  onDownloadResume,
}: VersionActionMenuProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" disabled={disabled}>
          <MoreVertical className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={onCopyResume} disabled={disabled}>
          <Copy className="mr-2 size-4" />
          Copy resume
        </DropdownMenuItem>
        <DropdownMenuItem onClick={onDownloadResume} disabled={!isPinned || disabled}>
          <Download className="mr-2 size-4" />
          Download resume
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

