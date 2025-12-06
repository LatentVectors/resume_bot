"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({
  content,
  className = "",
}: MarkdownRendererProps) {
  return (
    <div
      className={`prose prose-neutral dark:prose-invert max-w-none
        prose-headings:font-semibold prose-headings:tracking-tight
        prose-h1:text-2xl prose-h1:border-b prose-h1:border-border prose-h1:pb-2 prose-h1:mb-4
        prose-h2:text-xl prose-h2:mt-6 prose-h2:mb-3
        prose-h3:text-lg prose-h3:mt-5 prose-h3:mb-2
        prose-p:leading-relaxed prose-p:my-3
        prose-ul:my-3 prose-ol:my-3
        prose-li:my-1
        prose-strong:font-semibold
        prose-blockquote:border-l-primary prose-blockquote:bg-muted/50 prose-blockquote:py-1 prose-blockquote:px-4 prose-blockquote:not-italic
        prose-code:bg-zinc-100 prose-code:text-zinc-800 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:before:content-none prose-code:after:content-none dark:prose-code:bg-zinc-800 dark:prose-code:text-zinc-200
        prose-pre:bg-zinc-100 prose-pre:text-zinc-800 prose-pre:border prose-pre:border-zinc-200 dark:prose-pre:bg-zinc-800 dark:prose-pre:text-zinc-200 dark:prose-pre:border-zinc-700
        prose-hr:border-border prose-hr:my-6
        ${className}`}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: (props) => (
            <a
              {...props}
              className="text-primary hover:underline"
              target="_blank"
              rel="noopener noreferrer"
            />
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
