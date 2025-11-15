"use client";

import { useState, useCallback } from "react";
import { ChatContainer, ChatMessages, ChatForm } from "@/components/ui/chat";
import { MessageList } from "@/components/ui/message-list";
import { MessageInput } from "@/components/ui/message-input";
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
    <ChatContainer className="flex h-full flex-col">
      {/* Quota Error Banner */}
      {quotaError && (
        <Alert className="m-4 border-destructive bg-destructive/10">
          <AlertDescription className="text-destructive">
            {quotaError}
          </AlertDescription>
        </Alert>
      )}

      {/* Message Container */}
      <div className="flex-1 overflow-y-auto p-4 h-[calc(100vh-400px)]">
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

      {/* Loading Indicator */}
      {isLoading && (
        <div className="flex items-center gap-2 border-t px-4 py-2 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          <span>Thinking...</span>
        </div>
      )}

      {/* Chat Input */}
      <ChatForm
        isPending={isSubmitting || isLoading}
        handleSubmit={handleSubmit}
        className="border-t"
      >
        {() => (
          <div className="p-4">
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
    </ChatContainer>
  );
}

