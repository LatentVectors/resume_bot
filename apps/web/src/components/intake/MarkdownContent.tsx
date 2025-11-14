"use client";

interface MarkdownContentProps {
  content: string;
  className?: string;
}

/**
 * Simple markdown content renderer.
 * For now, renders as pre-formatted text preserving whitespace.
 * Can be enhanced with a markdown library later if needed.
 */
export function MarkdownContent({ content, className = "" }: MarkdownContentProps) {
  if (!content || content.trim() === "") {
    return null;
  }

  // Parse JSON string if needed
  let parsedContent = content;
  try {
    const parsed = JSON.parse(content);
    if (typeof parsed === "string") {
      parsedContent = parsed;
    }
  } catch {
    // Not JSON, use as-is
  }

  return (
    <div className={`whitespace-pre-wrap ${className}`}>
      {parsedContent}
    </div>
  );
}

