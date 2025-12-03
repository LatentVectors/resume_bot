"use client";

import dynamic from "next/dynamic";
import { Alert, AlertDescription } from "@/components/ui/alert";

export interface PDFPreviewProps {
  url: string | null;
  isLoading?: boolean;
  error?: string | null;
}

// Dynamically import the PDF renderer with SSR disabled to avoid DOMMatrix error
const PDFRenderer = dynamic(() => import("./PDFRenderer"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full items-center justify-center">
      <div className="text-muted-foreground">Loading PDF viewer...</div>
    </div>
  ),
});

export function PDFPreview({ url, isLoading, error }: PDFPreviewProps) {
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-muted-foreground">Loading PDF preview...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <Alert>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!url) {
    return (
      <div className="flex h-full items-center justify-center">
        <Alert>
          <AlertDescription>
            No resume version available yet. Use the chat or edit the Resume
            Content tab to create one.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return <PDFRenderer url={url} />;
}

