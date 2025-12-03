"use client";

import { useState, useCallback } from "react";
import { ChatContainer, ChatMessages, ChatForm } from "@/components/ui/chat";
import { MessageList } from "@/components/ui/message-list";
import { MessageInput } from "@/components/ui/message-input";
import { ScrollFadeContainer } from "@/components/ui/scroll-fade-container";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2 } from "lucide-react";
import type { Message } from "@/components/ui/chat-message";

interface ChatMessage {
  role: "user" | "assistant" | "tool";
  content: string;
  tool_calls?: Array<{ [key: string]: unknown }> | null;
  tool_call_id?: string | null;
}

interface ChatInterfaceProps {
  jobId: number;
  sessionId: number;
  messages: ChatMessage[];
  onMessagesChange: (messages: ChatMessage[]) => void;
  onSendMessage: (message: string) => Promise<void>;
  isLoading: boolean;
  quotaError: string | null;
  onQuotaErrorDismiss: () => void;
}

/**
 * Convert API message format to Chat component Message format
 */
function convertToChatMessage(
  msg: ChatMessage,
  index: number
): Message | null {
  // Skip assistant messages that only contain tool calls (no content text)
  if (msg.role === "assistant" && !msg.content && msg.tool_calls) {
    return null;
  }

  // Convert tool messages to a simple message format
  if (msg.role === "tool") {
    return {
      id: `tool-${index}`,
      role: "assistant", // Display tool messages as assistant messages
      content: msg.content || "",
      createdAt: new Date(),
    };
  }

  return {
    id: `${msg.role}-${index}`,
    role: msg.role as "user" | "assistant",
    content: msg.content || "",
    createdAt: new Date(),
  };
}

export function ChatInterface({
  messages,
  onMessagesChange,
  onSendMessage,
  isLoading,
  quotaError,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Convert messages to Chat component format
  const chatMessages: Message[] = messages
    .map((msg, index) => convertToChatMessage(msg, index))
    .filter((msg): msg is Message => msg !== null);

  const handleSubmit = useCallback(
    async (e?: { preventDefault?: () => void }) => {
      e?.preventDefault?.();
      if (!input.trim() || isSubmitting) return;

      const userMessage: ChatMessage = {
        role: "user",
        content: input.trim(),
      };

      // Add user message to messages immediately
      const updatedMessages = [...messages, userMessage];
      onMessagesChange(updatedMessages);
      setInput("");
      setIsSubmitting(true);

      try {
        await onSendMessage(input.trim());
      } catch (error) {
        console.error("Failed to send message:", error);
        // Don't remove user message on error (per spec)
      } finally {
        setIsSubmitting(false);
      }
    },
    [input, isSubmitting, messages, onMessagesChange, onSendMessage]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
    },
    []
  );

  const isEmpty = chatMessages.length === 0;
  const isTyping = isLoading && chatMessages.length > 0;

  return (
    <ChatContainer className="h-full">
      {/* Message Container - Scrollable with fade indicators (grid row 1: 1fr) */}
      <ScrollFadeContainer
        className="min-h-0"
        scrollClassName="flex flex-col"
        topGradientHeight={32}
        bottomGradientHeight={80}
        fadeThreshold={100}
      >
        {/* Quota Error Banner - Sticky at top of scrollable area */}
        {quotaError && (
          <Alert className="my-4 mr-4 ml-0 border-destructive bg-destructive/10 shrink-0">
            <AlertDescription className="text-destructive">
              {quotaError}
            </AlertDescription>
          </Alert>
        )}

        {/* Messages content */}
        <div className="flex-1 min-h-0">
          <div className="pr-4 pt-4">
            {isEmpty ? (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                <div className="text-center">
                  <p className="mb-2">Start a conversation with the Resume Agent</p>
                  <p className="text-sm">Ask for resume changes...</p>
                </div>
              </div>
            ) : (
              <ChatMessages messages={chatMessages}>
                <MessageList messages={chatMessages} isTyping={isTyping} />
              </ChatMessages>
            )}
          </div>
        </div>
      </ScrollFadeContainer>

      {/* Loading Indicator and Chat Input - Fixed at bottom (grid row 2: auto) */}
      <div className="shrink-0">
        {isLoading && (
          <div className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            <span>Thinking...</span>
          </div>
        )}

        {/* Chat Input - Fixed at bottom */}
        <ChatForm
          isPending={isSubmitting || isLoading}
          handleSubmit={handleSubmit}
        >
          {() => (
            <div className="px-4 pb-4">
              <MessageInput
                value={input}
                onChange={handleInputChange}
                placeholder="Ask for resume changes..."
                isGenerating={isLoading}
                allowAttachments={false}
              />
            </div>
          )}
        </ChatForm>
      </div>
    </ChatContainer>
  );
}

