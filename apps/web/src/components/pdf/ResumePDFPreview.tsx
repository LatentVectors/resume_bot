"use client";

/**
 * Resume PDF Preview Component
 *
 * Generates and displays a PDF preview of resume data client-side.
 * Uses dynamic imports to avoid SSR issues with PDF generation.
 */

import { useEffect, useCallback, useState, useRef } from "react";
import dynamic from "next/dynamic";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";
import type { ResumeData } from "@resume/database/types";

// Dynamically import the PDF renderer to avoid SSR issues
const PDFRenderer = dynamic(() => import("@/components/intake/PDFRenderer"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center">
      <div className="text-muted-foreground">Loading PDF viewer...</div>
    </div>
  ),
});

interface ResumePDFPreviewProps {
  /** Resume data to render */
  resumeData: ResumeData | null;
  /** Whether to auto-generate on mount/data change */
  autoGenerate?: boolean;
  /** Optional class name for the container */
  className?: string;
}

/**
 * Client-side PDF preview for resume data.
 *
 * Generates the PDF in the browser using @react-pdf/renderer
 * and displays it using react-pdf.
 */
export function ResumePDFPreview({
  resumeData,
  autoGenerate = true,
  className,
}: ResumePDFPreviewProps) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Use ref to track previous URL for cleanup without causing re-renders
  const previousUrlRef = useRef<string | null>(null);

  // Generate PDF from resume data
  const generatePdf = useCallback(async () => {
    if (!resumeData) {
      setPdfUrl(null);
      return;
    }

    setIsGenerating(true);
    setError(null);

    try {
      // Dynamic import of @react-pdf/renderer to avoid SSR issues
      const { pdf } = await import("@react-pdf/renderer");
      const { ResumePDF } = await import("@/components/pdf/ResumePDF");

      // Generate the PDF blob
      const document = ResumePDF({ data: resumeData });
      const blob = await pdf(document).toBlob();

      // Revoke old URL if exists (using ref to avoid dependency cycle)
      if (previousUrlRef.current) {
        URL.revokeObjectURL(previousUrlRef.current);
      }

      // Create new URL
      const url = URL.createObjectURL(blob);
      previousUrlRef.current = url;
      setPdfUrl(url);
    } catch (err) {
      console.error("Failed to generate PDF:", err);
      setError(err instanceof Error ? err.message : "Failed to generate PDF");
      setPdfUrl(null);
    } finally {
      setIsGenerating(false);
    }
  }, [resumeData]); // Only depend on resumeData, not pdfUrl

  // Auto-generate on mount or when data changes
  useEffect(() => {
    if (autoGenerate && resumeData) {
      generatePdf();
    }
  }, [autoGenerate, resumeData, generatePdf]);

  // Cleanup URL on unmount
  useEffect(() => {
    return () => {
      if (previousUrlRef.current) {
        URL.revokeObjectURL(previousUrlRef.current);
      }
    };
  }, []);

  // Loading state
  if (isGenerating) {
    return (
      <div className={`flex h-full items-center justify-center ${className || ""}`}>
        <div className="flex flex-col items-center gap-2">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <div className="text-muted-foreground">Generating PDF...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className={`flex h-full flex-col items-center justify-center gap-4 ${className || ""}`}>
        <Alert variant="destructive" className="max-w-md">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button variant="outline" onClick={generatePdf}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Retry
        </Button>
      </div>
    );
  }

  // No data state
  if (!resumeData) {
    return (
      <div className={`flex h-full items-center justify-center ${className || ""}`}>
        <Alert>
          <AlertDescription>
            No resume data available. Create or select a resume version to preview.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // No URL yet (waiting for generation)
  if (!pdfUrl) {
    return (
      <div className={`flex h-full flex-col items-center justify-center gap-4 ${className || ""}`}>
        <Alert>
          <AlertDescription>
            PDF not yet generated. Click the button below to generate a preview.
          </AlertDescription>
        </Alert>
        <Button onClick={generatePdf}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Generate PDF
        </Button>
      </div>
    );
  }

  // Show PDF preview
  return (
    <div className={className}>
      <PDFRenderer url={pdfUrl} />
    </div>
  );
}

export default ResumePDFPreview;

