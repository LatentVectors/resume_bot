"use client";

import { useRef } from "react";
import {
  ThreadPrimitive,
  ComposerPrimitive,
  MessagePrimitive,
} from "@assistant-ui/react";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useLangGraphRuntime } from "@assistant-ui/react-langgraph";

import { createThread, getThreadState, sendMessage } from "@/lib/langgraph";
import { MarkdownRenderer } from "@/components/intake/MarkdownRenderer";
import { useMessagePartText } from "@assistant-ui/react";

interface ResumeChatProps {
  jobId: number;
  initialThreadId: string | null;
  onThreadCreated: (threadId: string) => void;
  context: {
    job_id: number;
    user_id: number;
    gap_analysis: string;
    stakeholder_analysis: string;
    work_experience: string;
    selected_version_id: number | null;
    template_name: string;
    parent_version_id: number | null;
  };
}

export function ResumeChat({
  initialThreadId,
  onThreadCreated,
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

  const AssistantMessage = () => (
    <MessagePrimitive.Root>
      <div className="flex flex-col items-start mb-4 pl-0">
        <div className="bg-muted text-foreground rounded-lg p-3 text-sm max-w-[70%]">
          <MessagePrimitive.Parts
            components={{
              Text: MarkdownText,
            }}
          />
        </div>
      </div>
    </MessagePrimitive.Root>
  );

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ThreadPrimitive.Root className="flex h-full flex-col">
        <ThreadPrimitive.Viewport className="flex-1 overflow-y-auto min-h-0 pr-4 pb-4 pt-4 scrollbar-minimal">
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
        <div className="border-t shrink-0">
          <ComposerPrimitive.Root className="p-4">
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
