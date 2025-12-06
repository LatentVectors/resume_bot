/**
 * Server-side LangGraph helpers for invoking stateless agents.
 * Do not import this file in client components.
 */

import { Client } from "@langchain/langgraph-sdk";

/**
 * Work experience enhancement suggestions from the LangGraph agent.
 */
interface WorkExperienceEnhancementSuggestions {
  experience_updates: Array<{
    experience_id: number;
    proposed_changes: Array<{
      field: string;
      original: string;
      proposed: string;
      rationale: string;
    }>;
  }>;
}

const LANGGRAPH_API_URL = process.env["LANGGRAPH_API_URL"];
const LANGCHAIN_API_KEY = process.env["LANGCHAIN_API_KEY"];

// Log configuration on startup (only in development)
if (process.env.NODE_ENV === "development") {
  console.log("[LangGraph] API URL:", LANGGRAPH_API_URL || "(not set)");
  console.log("[LangGraph] API Key:", LANGCHAIN_API_KEY ? "(set)" : "(not set)");
}

if (!LANGGRAPH_API_URL) {
  console.error("[LangGraph] LANGGRAPH_API_URL is not set in environment variables");
}

const client = new Client({
  apiUrl: LANGGRAPH_API_URL,
  apiKey: LANGCHAIN_API_KEY,
});

export async function runGapAnalysis(input: {
  job_description: string;
  work_experience: string;
}): Promise<string> {
  if (!LANGGRAPH_API_URL) {
    throw new Error("LANGGRAPH_API_URL is not configured. Please set it in .env.local");
  }

  try {
    // Run as threadless (stateless) execution
    const result = await client.runs.wait(
      null, // No thread ID for stateless runs
      "gap_analysis",
      { input }
    );

    return (result as { analysis?: string }).analysis || "";
  } catch (error) {
    console.error("[LangGraph] Gap analysis failed:", error);
    console.error("[LangGraph] Attempted to connect to:", LANGGRAPH_API_URL);
    throw error;
  }
}

export async function runStakeholderAnalysis(input: {
  job_description: string;
  work_experience: string;
}): Promise<string> {
  if (!LANGGRAPH_API_URL) {
    throw new Error("LANGGRAPH_API_URL is not configured. Please set it in .env.local");
  }

  try {
    const result = await client.runs.wait(null, "stakeholder_analysis", {
      input,
    });

    return (result as { analysis?: string }).analysis || "";
  } catch (error) {
    console.error("[LangGraph] Stakeholder analysis failed:", error);
    console.error("[LangGraph] Attempted to connect to:", LANGGRAPH_API_URL);
    throw error;
  }
}

export async function runExperienceExtraction(input: {
  thread_id: string;
  work_experience: string;
}): Promise<WorkExperienceEnhancementSuggestions> {
  const result = await client.runs.wait(null, "experience_extraction", {
    input,
  });

  return (result as { suggestions?: WorkExperienceEnhancementSuggestions })
    .suggestions as WorkExperienceEnhancementSuggestions;
}

export async function runJobDetailsExtraction(input: {
  job_description: string;
}): Promise<{ title: string | null; company: string | null }> {
  const result = await client.runs.wait(null, "job_details_extraction", {
    input,
  });

  const typedResult = result as { title?: string; company?: string };
  return {
    title: typedResult.title || null,
    company: typedResult.company || null,
  };
}

