"use client";

import { useMemo } from "react";
import { usePDF } from "@react-pdf/renderer";
import { ResumePDF } from "@/components/pdf/ResumePDF";
import type { ResumeData } from "@resume/database/types";

interface PDFPreviewContentProps {
  resumeData: ResumeData;
}

export function PDFPreviewContent({ resumeData }: PDFPreviewContentProps) {
  const document = useMemo(() => <ResumePDF data={resumeData} />, [resumeData]);
  const [instance] = usePDF({ document });

  if (instance.loading) {
    return (
      <div className="flex h-full min-h-[400px] items-center justify-center bg-slate-50">
        <div className="text-muted-foreground">Generating PDF...</div>
      </div>
    );
  }

  if (instance.error) {
    return (
      <div className="flex h-full min-h-[400px] items-center justify-center bg-red-50">
        <div className="text-red-600">
          Error generating PDF: {instance.error.message}
        </div>
      </div>
    );
  }

  if (!instance.url) {
    return (
      <div className="flex h-full min-h-[400px] items-center justify-center bg-slate-50">
        <div className="text-muted-foreground">Preparing PDF...</div>
      </div>
    );
  }

  // Append PDF viewer parameters to hide toolbar and navigation panes
  const pdfUrl = `${instance.url}#toolbar=0&navpanes=0&scrollbar=0&view=FitH`;

  return (
    <iframe
      src={pdfUrl}
      className="h-full w-full"
      style={{ border: "none" }}
      title="Resume PDF Preview"
    />
  );
}
