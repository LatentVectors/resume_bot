/**
 * Hook for client-side PDF generation.
 *
 * Uses @react-pdf/renderer to generate PDFs from resume data.
 */

import { useState, useCallback, useRef } from "react";
import { pdf } from "@react-pdf/renderer";
import { ResumePDF } from "@/components/pdf/ResumePDF";
import type { ResumeData } from "@resume/database/types";

export interface PdfGenerationState {
  isGenerating: boolean;
  error: string | null;
  pdfUrl: string | null;
}

export interface PdfGenerationActions {
  generatePdf: (data: ResumeData) => Promise<string | null>;
  downloadPdf: (data: ResumeData, filename: string) => Promise<void>;
  clearPdf: () => void;
}

export type UsePdfGenerationReturn = PdfGenerationState & PdfGenerationActions;

/**
 * Hook for generating PDFs from resume data.
 *
 * @returns State and actions for PDF generation
 *
 * @example
 * ```tsx
 * const { pdfUrl, isGenerating, error, generatePdf, downloadPdf } = usePdfGeneration();
 *
 * // Generate PDF for preview
 * await generatePdf(resumeData);
 *
 * // Download PDF
 * await downloadPdf(resumeData, "my-resume.pdf");
 * ```
 */
export function usePdfGeneration(): UsePdfGenerationReturn {
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  
  // Use ref to track previous URL for cleanup without causing callback recreation
  const previousUrlRef = useRef<string | null>(null);

  /**
   * Generate a PDF blob from resume data.
   */
  const generatePdfBlob = useCallback(async (data: ResumeData): Promise<Blob> => {
    const document = ResumePDF({ data });
    const blob = await pdf(document).toBlob();
    return blob;
  }, []);

  /**
   * Generate a PDF and create an object URL for preview.
   * Returns the URL or null if generation fails.
   */
  const generatePdf = useCallback(
    async (data: ResumeData): Promise<string | null> => {
      setIsGenerating(true);
      setError(null);

      try {
        // Revoke previous URL if exists (using ref to avoid dependency cycle)
        if (previousUrlRef.current) {
          URL.revokeObjectURL(previousUrlRef.current);
        }

        const blob = await generatePdfBlob(data);
        const url = URL.createObjectURL(blob);
        previousUrlRef.current = url;
        setPdfUrl(url);
        return url;
      } catch (err) {
        console.error("Failed to generate PDF:", err);
        const message = err instanceof Error ? err.message : "Failed to generate PDF";
        setError(message);
        setPdfUrl(null);
        return null;
      } finally {
        setIsGenerating(false);
      }
    },
    [generatePdfBlob]
  );

  /**
   * Generate and download a PDF.
   */
  const downloadPdf = useCallback(
    async (data: ResumeData, filename: string): Promise<void> => {
      setIsGenerating(true);
      setError(null);

      try {
        const blob = await generatePdfBlob(data);
        const url = URL.createObjectURL(blob);

        // Create download link
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Cleanup
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error("Failed to download PDF:", err);
        const message = err instanceof Error ? err.message : "Failed to download PDF";
        setError(message);
        throw err;
      } finally {
        setIsGenerating(false);
      }
    },
    [generatePdfBlob]
  );

  /**
   * Clear the current PDF URL and state.
   */
  const clearPdf = useCallback(() => {
    if (previousUrlRef.current) {
      URL.revokeObjectURL(previousUrlRef.current);
      previousUrlRef.current = null;
    }
    setPdfUrl(null);
    setError(null);
  }, []);

  return {
    isGenerating,
    error,
    pdfUrl,
    generatePdf,
    downloadPdf,
    clearPdf,
  };
}

/**
 * Generate a standard resume filename.
 *
 * Format: Resume - {company} - {title} - {name} - {yyyy_mm_dd}.pdf
 */
export function generateResumeFilename(
  companyName: string | null | undefined,
  jobTitle: string | null | undefined,
  fullName: string | null | undefined
): string {
  const sanitize = (value: string | null | undefined): string => {
    if (!value) return "Unknown";
    return value
      .trim()
      .replace(/[/\\:*?"<>|]/g, "-")
      .replace(/\s+/g, " ");
  };

  const company = sanitize(companyName) || "Unknown Company";
  const title = sanitize(jobTitle) || "Unknown Title";
  const name = sanitize(fullName) || "Unknown Name";

  const now = new Date();
  const dateStr = `${now.getFullYear()}_${String(now.getMonth() + 1).padStart(
    2,
    "0"
  )}_${String(now.getDate()).padStart(2, "0")}`;

  return `Resume - ${company} - ${title} - ${name} - ${dateStr}.pdf`;
}

