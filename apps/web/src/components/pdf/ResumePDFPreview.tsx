"use client";

import dynamic from "next/dynamic";
import { Alert, AlertDescription } from "@/components/ui/alert";
import type { ResumeData } from "@resume/database/types";

// Dynamically import the PDF content component to avoid SSR issues
const PDFPreviewContent = dynamic(
  () => import("./PDFPreviewContent").then((mod) => mod.PDFPreviewContent),
  {
    ssr: false,
    loading: () => (
      <div className="flex h-full min-h-[400px] items-center justify-center bg-slate-50">
        <div className="text-muted-foreground">Loading PDF viewer...</div>
      </div>
    ),
  }
);

interface ResumePDFPreviewProps {
  resumeData: ResumeData | null;
  className?: string;
}

export function ResumePDFPreview({
  resumeData,
  className,
}: ResumePDFPreviewProps) {
  if (!resumeData) {
    return (
      <div className={className}>
        <Alert>
          <AlertDescription>
            No resume data available. Create or select a resume version to
            preview.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className={`flex flex-col ${className ?? ""}`}>
      <div className="flex-1 min-h-0 overflow-hidden rounded-lg border border-slate-200 bg-white">
        <PDFPreviewContent resumeData={resumeData} />
      </div>
    </div>
  );
}

export default ResumePDFPreview;
