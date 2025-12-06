/**
 * Client-side LangGraph helpers for interacting with the LangGraph API.
 */

import { Client } from "@langchain/langgraph-sdk";
import type { LangChainMessage } from "@assistant-ui/react-langgraph";

const createClient = () => {
  const apiUrl =
    process.env["NEXT_PUBLIC_LANGGRAPH_API_URL"] ||
    `${typeof window !== "undefined" ? window.location.origin : "http://localhost:3000"}/api/langgraph`;
  return new Client({ apiUrl });
};

export const createThread = async () => {
  const client = createClient();
  return client.threads.create();
};

export const getThreadState = async (threadId: string) => {
  const client = createClient();
  return client.threads.getState(threadId);
};

export interface SendMessageConfig {
  context?: Record<string, unknown>;
}

const DEFAULT_ASSISTANT_ID = "resume_refinement";

export const sendMessage = async (params: {
  threadId: string;
  messages: LangChainMessage;
  config?: SendMessageConfig;
}) => {
  const client = createClient();
  const assistantId =
    process.env["NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID"] || DEFAULT_ASSISTANT_ID;
  return client.runs.stream(params.threadId, assistantId, {
    input: {
      messages: params.messages,
    },
    streamMode: "messages",
    config: params.config?.context
      ? { configurable: params.config.context }
      : undefined,
  });
};

