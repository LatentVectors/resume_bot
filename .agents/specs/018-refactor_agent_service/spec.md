# Agent Service Refactoring Sprint

## Overview

Refactor all LLM-powered features from the FastAPI service into a dedicated agents directory, deployed independently via LangGraph Deploy on LangSmith Cloud. This consolidates AI capabilities into a single service with a runtime environment optimized for agent deployment.

## Deployment Architecture

- **Agents Service**: Deployed to LangSmith Cloud via LangGraph Deploy
- **Next.js Frontend**: Deployed to Vercel (requires `NEXT_PUBLIC_LANGGRAPH_API_URL` and `NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID` env vars)
- **FastAPI Backend**: Existing deployment (workflows.py removed after migration)

## Directory Structure

All agents are defined in the `apps/agents` directory using a single `langgraph.json` with multiple graphs. Shared utilities live in a `shared/` subdirectory.

```
apps/agents/
├── .env.example          # Documents required environment variables
├── langgraph.json        # Defines all agent graphs
├── pyproject.toml
├── prompts/              # JSON prompt files (copied from apps/api/prompts/)
│   ├── extract_experience_updates.json
│   ├── gap_analysis.json
│   ├── resume_alignment_workflow.json
│   └── stakeholder_analysis.json
├── src/
│   ├── shared/           # Shared utilities
│   │   ├── __init__.py
│   │   ├── models.py     # Pydantic models for structured output
│   │   ├── prompts.py    # Prompt loading logic
│   │   ├── formatters.py # Experience formatting utilities
│   │   ├── llm.py        # OpenRouter model initialization
│   │   └── tools.py      # Shared tool definitions
│   ├── resume_refinement/
│   │   ├── __init__.py
│   │   └── graph.py
│   ├── gap_analysis/
│   │   ├── __init__.py
│   │   └── graph.py
│   ├── stakeholder_analysis/
│   │   ├── __init__.py
│   │   └── graph.py
│   ├── experience_extraction/
│   │   ├── __init__.py
│   │   └── graph.py
│   └── job_details_extraction/
│       ├── __init__.py
│       └── graph.py
```

**langgraph.json Configuration:**

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "dependencies": ["."],
  "graphs": {
    "resume_refinement": "./src/resume_refinement/graph.py:graph",
    "gap_analysis": "./src/gap_analysis/graph.py:graph",
    "stakeholder_analysis": "./src/stakeholder_analysis/graph.py:graph",
    "experience_extraction": "./src/experience_extraction/graph.py:graph",
    "job_details_extraction": "./src/job_details_extraction/graph.py:graph"
  },
  "env": ".env"
}
```

## Dependencies

### Python (apps/agents/pyproject.toml)

```toml
[project]
dependencies = [
    "langgraph>=0.2.0",
    "langchain-openai>=0.2.0",
    "langchain-core>=0.3.0",
    "langgraph-sdk>=0.1.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]
```

### Next.js (apps/web/package.json)

```json
{
  "dependencies": {
    "@assistant-ui/react": "^0.7.0",
    "@assistant-ui/react-langgraph": "^0.7.0",
    "@langchain/langgraph-sdk": "^0.0.36"
  }
}
```

## Environment Variables

### Agents Service (.env.example)

```bash
# OpenRouter API Key (used for all LLM calls)
OPENROUTER_API_KEY=your_openrouter_api_key

# LangGraph API URL (for SDK calls to fetch thread state)
# Used by experience_extraction to read messages from resume_refinement threads
LANGGRAPH_API_URL=http://localhost:2024

# Optional: OpenRouter headers
OPENROUTER_HTTP_REFERER=
OPENROUTER_X_TITLE=
```

### Next.js Frontend (.env.local)

```bash
# LangGraph API URL
# For development (direct connection, no API key required):
NEXT_PUBLIC_LANGGRAPH_API_URL=http://localhost:2024

# For production (through proxy with API key):
# LANGGRAPH_API_URL=https://your-langgraph-deployment.langsmith.dev
# LANGCHAIN_API_KEY=your_api_key

# Assistant ID (graph name)
NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID=resume_refinement
```

**Note**: All LLM calls go through OpenRouter, not direct OpenAI or Google API keys.

## OpenRouter Model Initialization

All agents use OpenRouter via the OpenAI-compatible API. Initialize models in `src/shared/llm.py`:

```python
from langchain_openai import ChatOpenAI
import os

def get_openrouter_model(model_id: str) -> ChatOpenAI:
    """Initialize a ChatOpenAI model using OpenRouter."""
    return ChatOpenAI(
        model=model_id,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", ""),
            "X-Title": os.getenv("OPENROUTER_X_TITLE", ""),
        }
    )

# Example usage
llm = get_openrouter_model("google/gemini-2.5-pro")
```

## Model Configuration

Each agent uses a hardcoded model via OpenRouter matching the current implementation. The code structure should make it easy to add runtime configuration in the future, but runtime model switching is not implemented in this sprint.

| Agent                  | Model          | OpenRouter Model ID     |
| ---------------------- | -------------- | ----------------------- |
| resume_refinement      | Gemini 2.5 Pro | `google/gemini-2.5-pro` |
| gap_analysis           | GPT-4o         | `openai/gpt-4o`         |
| stakeholder_analysis   | GPT-4o         | `openai/gpt-4o`         |
| experience_extraction  | GPT-4o         | `openai/gpt-4o`         |
| job_details_extraction | GPT-4o Mini    | `openai/gpt-4o-mini`    |

## Agents Overview

### Stateful Agent (Thread Persistence Required)

**resume_refinement**

- Handles AI-assisted resume editing with tool-based update proposals
- Requires thread persistence between runs to maintain conversation context
- Thread ID stored in the `Job` table as `resume_chat_thread_id`
- The conversation is scoped to the job/job intake, not a specific resume version
- Uses LangSmith Cloud built-in checkpointing
- Uses `MessagesState` from LangGraph as base state
- Context values (job_id, user_id, etc.) passed via LangGraph runtime context using `context_schema` and `Runtime` object (modern approach replacing `InjectedToolArg`)

### Stateless Agents (Threadless Execution)

The following agents do not need to persist graph state between runs. They are invoked as threadless runs, and results are stored in the database after completion.

**gap_analysis**

- Analyzes fit between job requirements and user experience
- Identifies matched requirements, partial matches, gaps, and suggested clarifying questions
- Receives pre-formatted work experience data as input (caller formats before invoking)
- Run as background task; UI polls or uses webhooks for completion status
- Uses prompt: `gap_analysis.json`

**stakeholder_analysis**

- Analyzes hiring stakeholders based on job description and user experience
- Receives pre-formatted work experience data as input (caller formats before invoking)
- Run as background task
- Uses prompt: `stakeholder_analysis.json`

**experience_extraction**

- Extracts experience updates from resume refinement conversation
- Receives a `thread_id` as input
- Uses LangGraph SDK to fetch messages from the resume_refinement thread
- Requires `LANGGRAPH_API_URL` environment variable
- Processes messages to suggest updates to experience records
- Does not modify the original thread state
- Uses prompt: Inline system/user prompts (see `experience_extraction.py` lines 114-154)
- Returns structured output: `WorkExperienceEnhancementSuggestions`

**job_details_extraction**

- Extracts job title and company name from job description text
- Simple structured extraction, run as threadless execution
- Uses inline prompts (see `src/features/jobs/extraction.py` lines 20-29)
- Returns structured output: `TitleCompany`

## Pydantic Models

Copy the following Pydantic models to `apps/agents/src/shared/models.py`:

**From `experience_extraction.py`:**

- `WorkExperienceEnhancementSuggestions`
- `RoleOverviewUpdate`, `CompanyOverviewUpdate`, `SkillAdd`, `AchievementAdd`, `AchievementUpdate` (originally from `src.database`)

**From `src/features/jobs/extraction.py`:**

- `TitleCompany`

**From `resume_refinement.py`:**

- `ProposedExperience`

## Agent Input/Output Schemas

### resume_refinement

```python
from dataclasses import dataclass
from langgraph.graph import StateGraph, MessagesState
from langgraph.runtime import Runtime, get_runtime

@dataclass
class ResumeRefinementContext:
    """Runtime context for resume refinement agent.

    Passed via context_schema when building the graph and accessed
    via Runtime object in nodes and get_runtime() in tools.
    """
    job_id: int
    user_id: int
    gap_analysis: str
    stakeholder_analysis: str
    work_experience: str
    selected_version_id: int | None
    template_name: str
    parent_version_id: int | None

class ResumeRefinementState(MessagesState):
    """State for resume refinement agent (messages only, context via runtime)."""
    pass

# Graph construction with context_schema
builder = StateGraph(ResumeRefinementState, context_schema=ResumeRefinementContext)

# Accessing context in a node
def call_model(state: ResumeRefinementState, runtime: Runtime[ResumeRefinementContext]):
    job_id = runtime.context.job_id
    gap_analysis = runtime.context.gap_analysis
    # ... use context in node logic

# Accessing context in a tool
from langchain_core.tools import tool

@tool
def propose_resume_draft(title: str, professional_summary: str, ...) -> str:
    """Propose a resume draft."""
    runtime = get_runtime(ResumeRefinementContext)
    job_id = runtime.context.job_id
    user_id = runtime.context.user_id
    template_name = runtime.context.template_name
    # ... tool implementation

# Invoking the graph with context (used by frontend via LangGraph API)
graph.invoke(
    {"messages": [{"role": "user", "content": "..."}]},
    context=ResumeRefinementContext(
        job_id=123,
        user_id=456,
        gap_analysis="...",
        stakeholder_analysis="...",
        work_experience="...",
        selected_version_id=None,
        template_name="resume_000.html",
        parent_version_id=None,
    )
)
```

### gap_analysis

**Design Decision**: Receives pre-formatted work experience data as input. The caller (Next.js backend) is responsible for fetching and formatting experience data before invoking the agent. This keeps the agent simple and avoids circular dependencies with the database layer.

```python
from typing import TypedDict

class GapAnalysisInput(TypedDict):
    job_description: str
    work_experience: str  # Pre-formatted markdown string

class GapAnalysisOutput(TypedDict):
    analysis: str  # Markdown formatted analysis
```

### stakeholder_analysis

**Design Decision**: Same as gap_analysis - receives pre-formatted data.

```python
from typing import TypedDict

class StakeholderAnalysisInput(TypedDict):
    job_description: str
    work_experience: str  # Pre-formatted markdown string

class StakeholderAnalysisOutput(TypedDict):
    analysis: str  # Markdown formatted analysis
```

### experience_extraction

```python
from typing import TypedDict
from langgraph_sdk import get_client
import asyncio
import os

class ExperienceExtractionInput(TypedDict):
    thread_id: str  # LangGraph thread ID to fetch messages from
    work_experience: str  # Pre-formatted experience data for context

class ExperienceExtractionOutput(TypedDict):
    suggestions: WorkExperienceEnhancementSuggestions  # Structured suggestions

# Fetching messages from another thread using LangGraph SDK
async def fetch_thread_messages(thread_id: str) -> list:
    """Fetch messages from a resume_refinement thread."""
    client = get_client(url=os.getenv("LANGGRAPH_API_URL"))
    thread_state = await client.threads.get_state(thread_id)
    return thread_state["values"]["messages"]

# For synchronous contexts, use asyncio.run()
def fetch_thread_messages_sync(thread_id: str) -> list:
    """Synchronous wrapper for fetching thread messages."""
    return asyncio.run(fetch_thread_messages(thread_id))
```

### job_details_extraction

```python
from typing import TypedDict

class JobDetailsExtractionInput(TypedDict):
    job_description: str

class JobDetailsExtractionOutput(TypedDict):
    title: str | None
    company: str | None
```

## Tool Architecture (resume_refinement)

The `propose_resume_draft` tool:

1. Receives resume data as parameters from the LLM
2. Accesses runtime context via `get_runtime(ResumeRefinementContext)` for job_id, user_id, template_name, parent_version_id
3. Makes HTTP POST to FastAPI backend (`POST /api/v1/jobs/{job_id}/resumes`)
4. Returns only the IDs needed to look up the saved version:
   - `version_id` - Database ID of the created resume version
   - `version_index` - Monotonic version index for display

**Runtime Context Pattern**: Use `context_schema` when building the graph and `get_runtime()` within tools to access context values. This replaces the older `InjectedToolArg` pattern.

```python
from langchain_core.tools import tool
from langgraph.runtime import get_runtime
import httpx
import os

from shared.models import ProposedExperience

# Import the context schema
from .graph import ResumeRefinementContext

@tool
def propose_resume_draft(
    title: str,
    professional_summary: str,
    skills: list[str],
    experiences: list[ProposedExperience],
    education_ids: list[int],
    certification_ids: list[int],
) -> dict:
    """Propose a complete resume draft.

    Creates a new resume version with the proposed content.
    """
    # Access runtime context (no InjectedToolArg needed)
    runtime = get_runtime(ResumeRefinementContext)

    # Build request payload matching FastAPI ResumeCreate schema
    payload = {
        "template_name": runtime.context.template_name,
        "event_type": "generate",
        "parent_version_id": runtime.context.parent_version_id,
        "resume_json": {
            "name": "",  # Will be filled by backend from user record
        "title": title,
            "email": "",
            "phone": "",
            "linkedin_url": "",
        "professional_summary": professional_summary,
        "skills": skills,
            "experience": [
                {
                    "experience_id": exp.experience_id,
                    "title": exp.title,
                    "points": exp.points,
                }
                for exp in experiences
            ],
        "education_ids": education_ids,
        "certification_ids": certification_ids,
        },
    }

    # Call FastAPI backend to persist the version
    # Using existing endpoint: POST /api/v1/jobs/{job_id}/resumes
    api_base = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
    response = httpx.post(
        f"{api_base}/api/v1/jobs/{runtime.context.job_id}/resumes",
        json=payload,
        timeout=30.0,
    )
    response.raise_for_status()
    result = response.json()

    return {
        "version_id": result["id"],
        "version_index": result["version_index"],
        "message": f"Resume Draft Created: v{result['version_index']}",
    }
```

## Error Handling

Preserve the current error handling pattern (graceful degradation):

- Agents catch exceptions and log errors
- Return fallback values (empty strings, null values) rather than raising to caller
- Prevents errors from bubbling to UI
- Allows partial functionality even when some operations fail

**OpenRouter-Specific Handling**: Since we're using OpenRouter instead of direct OpenAI/Google APIs, error responses will come from OpenRouter. The error format may differ slightly. Handle rate limits and quota errors generically:

```python
from httpx import HTTPStatusError

try:
    response = llm.invoke(messages)
except HTTPStatusError as exc:
    if exc.response.status_code == 429:
        logger.error("Rate limit exceeded: %s", exc)
        return fallback_value
    raise
except Exception as exc:
    logger.exception("LLM call failed: %s", exc)
    return fallback_value
```

## Database Changes

Add `resume_chat_thread_id` column to the `Job` table:

- Type: `string` (nullable)
- Purpose: Stores the LangGraph thread ID for the resume refinement conversation
- Created when a user starts their first resume chat for a job

## API Architecture

### FastAPI Backend (Existing)

The FastAPI backend continues to handle all database operations. LangGraph agents make HTTP calls to these existing endpoints:

| Endpoint                        | Method | Purpose                          |
| ------------------------------- | ------ | -------------------------------- |
| `/api/v1/jobs/{job_id}/resumes` | POST   | Create resume version            |
| `/api/v1/experiences`           | GET    | Fetch user experiences           |
| `/api/v1/education`             | GET    | Fetch user education             |
| `/api/v1/certificates`          | GET    | Fetch user certifications        |
| `/api/v1/users/{id}`            | GET    | Fetch user profile               |
| `/api/v1/jobs/{job_id}`         | GET    | Fetch job details                |
| `/api/v1/jobs/{job_id}`         | PATCH  | Update job (including thread_id) |

### Next.js API Routes (New)

Create a LangGraph proxy route to forward requests to the LangGraph API. This enables:

- Adding API key authentication in production
- Rate limiting and request validation
- CORS handling

**Create `apps/web/src/app/api/[...path]/route.ts`:**

```typescript
import { NextRequest, NextResponse } from "next/server";

function getCorsHeaders() {
  return {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
    "Access-Control-Allow-Headers": "*",
  };
}

async function handleRequest(req: NextRequest, method: string) {
  try {
    const path = req.nextUrl.pathname.replace(/^\/?api\//, "");
    const url = new URL(req.url);
    const searchParams = new URLSearchParams(url.search);
    searchParams.delete("_path");
    searchParams.delete("nxtP_path");
    const queryString = searchParams.toString()
      ? `?${searchParams.toString()}`
      : "";

    const options: RequestInit = {
      method,
      headers: {
        "x-api-key": process.env["LANGCHAIN_API_KEY"] || "",
      },
    };

    if (["POST", "PUT", "PATCH"].includes(method)) {
      options.body = await req.text();
    }

    const res = await fetch(
      `${process.env["LANGGRAPH_API_URL"]}/${path}${queryString}`,
      options
    );

    return new NextResponse(res.body, {
      status: res.status,
      statusText: res.statusText,
      headers: {
        ...Object.fromEntries(res.headers),
        ...getCorsHeaders(),
      },
    });
  } catch (e: unknown) {
    const message = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}

export const GET = (req: NextRequest) => handleRequest(req, "GET");
export const POST = (req: NextRequest) => handleRequest(req, "POST");
export const PUT = (req: NextRequest) => handleRequest(req, "PUT");
export const PATCH = (req: NextRequest) => handleRequest(req, "PATCH");
export const DELETE = (req: NextRequest) => handleRequest(req, "DELETE");

export const OPTIONS = () => {
  return new NextResponse(null, {
    status: 204,
    headers: getCorsHeaders(),
  });
};
```

### Authentication (Future Sprint)

Authentication is not implemented in this sprint. Currently running locally for a single user.

**Future requirement**: Integrate Supabase auth to limit agent actions to only act on data belonging to the user who initiates the interaction. The agent must only be able to interact with and modify the authenticated user's data.

## Frontend Integration (assistant-ui)

The Next.js frontend uses [assistant-ui](https://www.assistant-ui.com/docs/runtimes/langgraph) with the LangGraph runtime for chat functionality. This replaces the previous shadcn-chatbot-kit approach.

### Helper Functions

**Create `apps/web/src/lib/langgraph.ts`:**

```typescript
import { Client } from "@langchain/langgraph-sdk";
import type { LangChainMessage } from "@assistant-ui/react-langgraph";

const createClient = () => {
  const apiUrl = process.env["NEXT_PUBLIC_LANGGRAPH_API_URL"] || "/api";
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

export const sendMessage = async (params: {
  threadId: string;
  messages: LangChainMessage;
  config?: SendMessageConfig;
}) => {
  const client = createClient();
  return client.runs.stream(
    params.threadId,
    process.env["NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID"]!,
    {
      input: {
        messages: params.messages,
      },
      streamMode: "messages",
      config: params.config?.context
        ? { configurable: params.config.context }
        : undefined,
    }
  );
};
```

### Resume Chat Component

**Create `apps/web/src/components/resume-chat/ResumeChat.tsx`:**

```typescript
"use client";

import { Thread } from "@assistant-ui/react";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { useLangGraphRuntime } from "@assistant-ui/react-langgraph";
import { useCallback, useEffect, useState } from "react";

import { createThread, getThreadState, sendMessage } from "@/lib/langgraph";

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
  jobId,
  initialThreadId,
  onThreadCreated,
  context,
}: ResumeChatProps) {
  const [isReady, setIsReady] = useState(false);

  const runtime = useLangGraphRuntime({
    stream: async (messages, { initialize }) => {
      const { externalId } = await initialize();
      if (!externalId) throw new Error("Thread not found");

      return sendMessage({
        threadId: externalId,
        messages,
        config: { context },
      });
    },

    create: async () => {
      // Create a new LangGraph thread
      const { thread_id } = await createThread();

      // Notify parent to persist thread_id to the Job record
      onThreadCreated(thread_id);

      return { externalId: thread_id };
    },

    load: async (externalId) => {
      // Load existing thread state
      const state = await getThreadState(externalId);
      return {
        messages: state.values.messages,
        interrupts: state.tasks?.[0]?.interrupts,
      };
    },
  });

  // Initialize with existing thread if available
  useEffect(() => {
    if (initialThreadId && !isReady) {
      // The runtime will call load() automatically when we set externalId
      setIsReady(true);
    }
  }, [initialThreadId, isReady]);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <Thread />
    </AssistantRuntimeProvider>
  );
}
```

### Page Integration

**Update the resume chat page to use the new component:**

```typescript
"use client";

import { useEffect, useState, useCallback } from "react";
import { ResumeChat } from "@/components/resume-chat/ResumeChat";

interface ResumeChatPageProps {
  params: { jobId: string };
}

export default function ResumeChatPage({ params }: ResumeChatPageProps) {
  const jobId = parseInt(params.jobId, 10);
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);

  // Fetch job data including existing thread_id
  useEffect(() => {
    async function fetchJob() {
      const response = await fetch(`/api/v1/jobs/${jobId}`);
      const data = await response.json();
      setJob(data);
      setLoading(false);
    }
    fetchJob();
  }, [jobId]);

  // Callback to persist new thread_id to the Job record
  const handleThreadCreated = useCallback(
    async (threadId: string) => {
      await fetch(`/api/v1/jobs/${jobId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ resume_chat_thread_id: threadId }),
      });

      // Update local state
      setJob((prev) =>
        prev ? { ...prev, resume_chat_thread_id: threadId } : prev
      );
    },
    [jobId]
  );

  if (loading || !job) {
    return <div>Loading...</div>;
  }

  // Build context for the agent
  const context = {
    job_id: job.id,
    user_id: job.user_id,
    gap_analysis: job.gap_analysis || "",
    stakeholder_analysis: job.stakeholder_analysis || "",
    work_experience: job.formatted_work_experience || "",
    selected_version_id: job.pinned_resume_version_id,
    template_name: "resume_000.html",
    parent_version_id: job.pinned_resume_version_id,
  };

  return (
    <div className="h-screen flex flex-col">
      <ResumeChat
        jobId={jobId}
        initialThreadId={job.resume_chat_thread_id}
        onThreadCreated={handleThreadCreated}
        context={context}
      />
    </div>
  );
}
```

### Thread Management Flow

1. **User opens resume chat for a job**
2. **Page fetches Job record** including `resume_chat_thread_id`
3. **If thread exists** (`initialThreadId` is set):
   - `useLangGraphRuntime` calls `load(externalId)` to restore conversation
   - Thread state (messages, interrupts) loaded from LangGraph API
4. **If no thread exists** (`initialThreadId` is null):
   - On first message, `useLangGraphRuntime` calls `create()`
   - New thread created via LangGraph API
   - `onThreadCreated` callback persists `thread_id` to Job record via PATCH
5. **On each message**:
   - `stream()` sends message to LangGraph with context
   - Context includes job_id, user_id, work_experience, etc.
   - Agent processes message and may invoke tools

### Stateless Workflow Invocation

For stateless agents (gap_analysis, stakeholder_analysis, etc.), invoke from the Next.js backend using the LangGraph SDK directly:

**Create `apps/web/src/lib/langgraph-server.ts`:**

```typescript
// Server-side only - do not import in client components
import { Client } from "@langchain/langgraph-sdk";

const client = new Client({
  apiUrl: process.env["LANGGRAPH_API_URL"],
  apiKey: process.env["LANGCHAIN_API_KEY"],
});

export async function runGapAnalysis(input: {
  job_description: string;
  work_experience: string;
}): Promise<string> {
  // Run as threadless (stateless) execution
  const result = await client.runs.wait(
    null, // No thread ID for stateless runs
    "gap_analysis",
    { input }
  );

  return result.values?.analysis || "";
}

export async function runStakeholderAnalysis(input: {
  job_description: string;
  work_experience: string;
}): Promise<string> {
  const result = await client.runs.wait(null, "stakeholder_analysis", {
    input,
  });

  return result.values?.analysis || "";
}

export async function runExperienceExtraction(input: {
  thread_id: string;
  work_experience: string;
}): Promise<WorkExperienceEnhancementSuggestions> {
  const result = await client.runs.wait(null, "experience_extraction", {
    input,
  });

  return result.values?.suggestions;
}

export async function runJobDetailsExtraction(input: {
  job_description: string;
}): Promise<{ title: string | null; company: string | null }> {
  const result = await client.runs.wait(null, "job_details_extraction", {
    input,
  });

  return {
    title: result.values?.title || null,
    company: result.values?.company || null,
  };
}
```

## Migration Tasks

### Code to Rewrite as LangGraph Agents

| Source File                                                                   | Destination                                       | Notes                                  |
| ----------------------------------------------------------------------------- | ------------------------------------------------- | -------------------------------------- |
| `apps/api/api/services/job_intake_service/workflows/resume_refinement.py`     | `apps/agents/src/resume_refinement/graph.py`      | Stateful, uses tools, runtime context  |
| `apps/api/api/services/job_intake_service/workflows/gap_analysis.py`          | `apps/agents/src/gap_analysis/graph.py`           | Stateless, receives pre-formatted data |
| `apps/api/api/services/job_intake_service/workflows/stakeholder_analysis.py`  | `apps/agents/src/stakeholder_analysis/graph.py`   | Stateless, receives pre-formatted data |
| `apps/api/api/services/job_intake_service/workflows/experience_extraction.py` | `apps/agents/src/experience_extraction/graph.py`  | Stateless, uses SDK to read thread     |
| `apps/api/src/features/jobs/extraction.py`                                    | `apps/agents/src/job_details_extraction/graph.py` | Stateless, structured output           |

### Shared Utilities to Copy/Move

| Source                                   | Destination                            | Notes                           |
| ---------------------------------------- | -------------------------------------- | ------------------------------- |
| `apps/api/prompts/*.json`                | `apps/agents/prompts/`                 | 4 JSON prompt files             |
| `apps/api/src/core/prompts/loader.py`    | `apps/agents/src/shared/prompts.py`    | Prompt loading logic            |
| `apps/api/src/core/prompts/names.py`     | `apps/agents/src/shared/prompts.py`    | PromptName enum                 |
| `apps/api/src/core/prompts/constants.py` | `apps/agents/src/shared/prompts.py`    | Update PROMPTS_DIR path         |
| `apps/api/src/shared/formatters.py`      | `apps/agents/src/shared/formatters.py` | Experience formatting utilities |
| Pydantic models (see above)              | `apps/agents/src/shared/models.py`     | Structured output models        |

**Prompt Path Update**: When copying prompts.py, update the PROMPTS_DIR constant:

```python
# Before (in apps/api)
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"

# After (in apps/agents)
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts"
# This resolves to: apps/agents/prompts/
```

Goal: Minimize dependencies on the existing `api` package. The agents package should be self-contained.

### Code to Remove (End of Sprint)

| File/Directory                                        | Reason                                       |
| ----------------------------------------------------- | -------------------------------------------- |
| `apps/api/api/routes/workflows.py`                    | All consumers migrated to LangGraph API      |
| `apps/api/api/services/job_intake_service/workflows/` | Rewritten as agents                          |
| `apps/agents/src/agent/graph.py`                      | Example Yoda agent (can be removed up front) |
| `apps/agents/tests/`                                  | No automated testing this sprint             |

### Frontend Updates

1. **Install assistant-ui packages:**

   ```bash
   cd apps/web
   npm install @assistant-ui/react @assistant-ui/react-langgraph @langchain/langgraph-sdk
   ```

2. **Remove shadcn-chatbot-kit** (if installed):

   ```bash
   npm uninstall @shadcn/chatbot-kit  # or similar package name
   ```

3. **Create new files:**

   - `apps/web/src/app/api/[...path]/route.ts` - LangGraph proxy
   - `apps/web/src/lib/langgraph.ts` - Client-side helpers
   - `apps/web/src/lib/langgraph-server.ts` - Server-side helpers
   - `apps/web/src/components/resume-chat/ResumeChat.tsx` - Chat component

4. **Update existing files:**
   - Resume chat page to use new `ResumeChat` component
   - Remove old workflow API calls in `apps/web/src/lib/api/workflows.ts`

## Testing

No automated unit or integration tests for this sprint. All functionality will be manually tested at the end of the sprint.

### Manual Testing Checklist

- [ ] Resume chat creates new thread on first message
- [ ] Thread ID persisted to Job record
- [ ] Subsequent visits restore conversation history
- [ ] `propose_resume_draft` tool creates resume version
- [ ] Gap analysis returns markdown analysis
- [ ] Stakeholder analysis returns markdown analysis
- [ ] Experience extraction reads thread and returns suggestions
- [ ] Job details extraction returns title/company

## Runtime Context Pattern Summary

The modern LangGraph approach for passing context to agents:

1. **Define context schema** using `@dataclass`
2. **Build graph** with `context_schema` parameter: `StateGraph(State, context_schema=ContextSchema)`
3. **Access in nodes** via `Runtime` parameter: `def node(state, runtime: Runtime[ContextSchema])`
4. **Access in tools** via `get_runtime()`: `runtime = get_runtime(ContextSchema)`
5. **Invoke with context**: `graph.invoke(input, context=ContextSchema(...))`

This replaces the older `InjectedToolArg` pattern and provides type-safe, immutable context throughout graph execution.

## Reference Links

- [assistant-ui LangGraph Integration](https://www.assistant-ui.com/docs/runtimes/langgraph)
- [LangGraph Runtime Context Documentation](https://langchain-ai.github.io/langgraph/concepts/low_level/#runtime-context)
- [LangGraph Deploy](https://langchain-ai.github.io/langgraph/cloud/deployment/)
