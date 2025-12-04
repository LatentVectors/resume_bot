"use client";

import { useRef, useEffect } from "react";
import {
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
  useMessage,
  useThread,
} from "@assistant-ui/react";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useLangGraphRuntime } from "@assistant-ui/react-langgraph";

import { createThread, getThreadState, sendMessage } from "@/lib/langgraph";
import { MarkdownRenderer } from "@/components/intake/MarkdownRenderer";
import { useMessagePartText } from "@assistant-ui/react";
import { ScrollFadeContainer } from "@/components/ui/scroll-fade-container";
import { Dot } from "lucide-react";

function TypingDots() {
  return (
    <div className="flex items-center -space-x-2.5 py-2 text-muted-foreground">
      <Dot className="h-5 w-5 animate-typing-dot-bounce" />
      <Dot className="h-5 w-5 animate-typing-dot-bounce [animation-delay:90ms]" />
      <Dot className="h-5 w-5 animate-typing-dot-bounce [animation-delay:180ms]" />
    </div>
  );
}

/**
 * Internal component that monitors messages for propose_resume_draft tool calls
 * and triggers a callback when a new resume version is created.
 */
function ResumeVersionMonitor({ onVersionCreated }: { onVersionCreated?: () => void }) {
  const messages = useThread((t) => t.messages);
  const isRunning = useThread((t) => t.isRunning);
  const wasRunningRef = useRef(false);
  const processedToolCallsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    // Detect transition from running to not running
    if (wasRunningRef.current && !isRunning && onVersionCreated) {
      // Check for new propose_resume_draft tool results in messages
      for (const msg of messages) {
        if (msg.role === "assistant" && msg.content) {
          for (const part of msg.content) {
            if (
              part.type === "tool-call" &&
              part.toolName === "propose_resume_draft" &&
              part.toolCallId &&
              !processedToolCallsRef.current.has(part.toolCallId)
            ) {
              // Mark this tool call as processed
              processedToolCallsRef.current.add(part.toolCallId);
              // Trigger callback to refetch resume versions
              onVersionCreated();
              break;
            }
          }
        }
      }
    }
    wasRunningRef.current = isRunning;
  }, [isRunning, messages, onVersionCreated]);

  return null;
}

interface ResumeChatProps {
  jobId: number;
  initialThreadId: string | null;
  onThreadCreated: (threadId: string) => void;
  onResumeVersionCreated?: () => void;
  context: {
    job_id: number;
    user_id: number;
    gap_analysis: string;
    stakeholder_analysis: string;
    work_experience: string;
    job_description: string;
    selected_version_id: number | null;
    template_name: string;
    parent_version_id: number | null;
  };
}

export function ResumeChat({
  initialThreadId,
  onThreadCreated,
  onResumeVersionCreated,
  context,
}: ResumeChatProps) {
  const threadIdRef = useRef<string | undefined>(initialThreadId ?? undefined);

  const runtime = useLangGraphRuntime({
    threadId: threadIdRef.current,
    stream: async (messages) => {
      if (!threadIdRef.current) {
        // Create a new LangGraph thread
        const { thread_id } = await createThread();
        threadIdRef.current = thread_id;

        // Notify parent to persist thread_id to the Job record
        onThreadCreated(thread_id);
      }

      return sendMessage({
        threadId: threadIdRef.current,
        messages,
        config: { context },
      });
    },
    onSwitchToNewThread: async () => {
      const { thread_id } = await createThread();
      threadIdRef.current = thread_id;
      onThreadCreated(thread_id);
    },
    onSwitchToThread: async (threadId) => {
      const state = await getThreadState(threadId);
      threadIdRef.current = threadId;
      return {
        messages: state.values.messages,
        interrupts: state.tasks?.[0]?.interrupts,
      };
    },
  });

  // Custom text component that renders markdown
  const MarkdownText = () => {
    const textPart = useMessagePartText();
    return <MarkdownRenderer content={textPart?.text || ""} />;
  };

  // Basic message components for assistant-ui
  const UserMessage = () => (
    <MessagePrimitive.Root>
      <div className="flex flex-col items-end mb-4 pl-0">
        <div className="bg-primary text-primary-foreground rounded-lg p-3 text-sm max-w-[70%]">
          <MessagePrimitive.Parts />
        </div>
      </div>
    </MessagePrimitive.Root>
  );

  const AssistantMessage = () => {
    const message = useMessage();
    const isInProgress = message.isLast && message.status?.type === "running";
    const hasContent = message.content && message.content.length > 0 && 
      message.content.some(part => part.type === "text" && part.text.length > 0);
    
    // Show typing dots if message is in progress but has no content yet
    if (isInProgress && !hasContent) {
      return (
        <MessagePrimitive.Root>
          <div className="w-full mb-4">
            <TypingDots />
          </div>
        </MessagePrimitive.Root>
      );
    }
    
    return (
      <MessagePrimitive.Root>
        <div className="w-full mb-4">
          <MessagePrimitive.Parts
            components={{
              Text: MarkdownText,
            }}
          />
        </div>
      </MessagePrimitive.Root>
    );
  };

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ResumeVersionMonitor onVersionCreated={onResumeVersionCreated} />
      <ThreadPrimitive.Root className="flex h-full flex-col">
        <ScrollFadeContainer
          className="flex-1 min-h-0"
          scrollClassName="pr-4 pt-4"
          topGradientHeight={32}
          bottomGradientHeight={96}
          fadeThreshold={80}
        >
          <ThreadPrimitive.Viewport className="min-h-0">
            <ThreadPrimitive.Empty>
              <div className="flex min-h-full items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <p className="mb-2">Start a conversation with the Resume Agent</p>
                  <p className="text-sm">Ask for resume changes...</p>
                </div>
              </div>
            </ThreadPrimitive.Empty>
            <ThreadPrimitive.Messages
              components={{
                UserMessage,
                AssistantMessage,
              }}
            />
          </ThreadPrimitive.Viewport>
        </ScrollFadeContainer>
        <div className="shrink-0">
          <ComposerPrimitive.Root className="px-4 pb-4">
            <ComposerPrimitive.Input
              placeholder="Ask for resume changes..."
              className="w-full rounded-xl border border-input bg-background p-3 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:border-primary focus-visible:outline-none"
            />
            <ComposerPrimitive.Send className="mt-2" />
          </ComposerPrimitive.Root>
        </div>
      </ThreadPrimitive.Root>
    </AssistantRuntimeProvider>
  );
}
