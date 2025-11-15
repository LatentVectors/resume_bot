"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  const [hasError, setHasError] = useState(false);

  // Reset error state when content changes
  useEffect(() => {
    setHasError(false);
  }, [content]);

  if (hasError) {
    // Fallback to plain text if markdown rendering fails
    return (
      <div className={className}>
        <pre className="whitespace-pre-wrap font-sans">{content}</pre>
      </div>
    );
  }

  try {
    return (
      <div className={`prose prose-sm max-w-none ${className}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Custom components to handle potential edge cases
            a: ({ node, ...props }) => (
              <a {...props} target="_blank" rel="noopener noreferrer" />
            ),
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  } catch (error) {
    console.error("Markdown rendering error:", error);
    setHasError(true);
    // Return fallback
    return (
      <div className={className}>
        <pre className="whitespace-pre-wrap font-sans">{content}</pre>
      </div>
    );
  }
}

