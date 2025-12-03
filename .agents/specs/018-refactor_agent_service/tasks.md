# Spec Tasks

## Parallelization Overview

```
PHASE 1 (Parallel)
├── Task 1: Agents Package Setup
├── Task 2: Database Changes
└── Task 8: Frontend Dependencies

PHASE 2 (Sequential - depends on Task 1)
└── Task 3: Shared Utilities

PHASE 3 (Parallel - depends on Task 3)
├── Task 4: gap_analysis Agent
├── Task 5: stakeholder_analysis Agent
├── Task 6: job_details_extraction Agent
├── Task 7: experience_extraction Agent
└── Task 9: resume_refinement Agent

PHASE 4 (Sequential - depends on Tasks 2, 8, and at least one agent)
└── Task 10: Frontend Integration

PHASE 5 (Sequential - after all integration complete)
└── Task 11: Cleanup & Verification
```

---

## Tasks

- [x] 1. Agents Package Setup

  - [x] 1.1 Create `apps/agents/pyproject.toml` with dependencies (langgraph, langchain-openai, langchain-core, langgraph-sdk, httpx, pydantic)
  - [x] 1.2 Create `apps/agents/langgraph.json` with all 5 graph definitions
  - [x] 1.3 Create `apps/agents/.env.example` documenting required env vars (OPENROUTER_API_KEY, LANGGRAPH_API_URL, FASTAPI_BASE_URL)
  - [x] 1.4 Copy prompt JSON files from `apps/api/prompts/` to `apps/agents/prompts/`
  - [x] 1.5 Remove example files: `apps/agents/src/agent/graph.py` and `apps/agents/tests/`
  - [x] 1.6 Create directory structure for all 5 agent modules with `__init__.py` files

- [x] 2. Database Changes

  - [x] 2.1 Add `resume_chat_thread_id` column (nullable string) to Job table in database schema
  - [x] 2.2 Update Job Pydantic model to include `resume_chat_thread_id` field
  - [x] 2.3 Update FastAPI PATCH `/api/v1/jobs/{job_id}` endpoint to accept `resume_chat_thread_id` updates

- [x] 3. Shared Utilities (`apps/agents/src/shared/`)

  - [x] 3.1 Create `llm.py` with `get_openrouter_model()` function
  - [x] 3.2 Create `prompts.py` with prompt loading logic (copy from `apps/api/src/core/prompts/`) and update PROMPTS_DIR path
  - [x] 3.3 Create `formatters.py` (copy from `apps/api/src/shared/formatters.py`)
  - [x] 3.4 Create `models.py` with Pydantic models: TitleCompany, ProposedExperience, WorkExperienceEnhancementSuggestions, RoleOverviewUpdate, CompanyOverviewUpdate, SkillAdd, AchievementAdd, AchievementUpdate
  - [x] 3.5 Create `__init__.py` exporting key utilities

- [x] 4. gap_analysis Agent

  - [x] 4.1 Create `apps/agents/src/gap_analysis/__init__.py`
  - [x] 4.2 Create `apps/agents/src/gap_analysis/graph.py` with GapAnalysisInput/Output schemas
  - [x] 4.3 Implement single-node graph that loads prompt, calls LLM (openai/gpt-4o), returns markdown analysis
  - [x] 4.4 Add error handling with graceful degradation (return empty string on failure)

- [x] 5. stakeholder_analysis Agent

  - [x] 5.1 Create `apps/agents/src/stakeholder_analysis/__init__.py`
  - [x] 5.2 Create `apps/agents/src/stakeholder_analysis/graph.py` with StakeholderAnalysisInput/Output schemas
  - [x] 5.3 Implement single-node graph that loads prompt, calls LLM (openai/gpt-4o), returns markdown analysis
  - [x] 5.4 Add error handling with graceful degradation (return empty string on failure)

- [x] 6. job_details_extraction Agent

  - [x] 6.1 Create `apps/agents/src/job_details_extraction/__init__.py`
  - [x] 6.2 Create `apps/agents/src/job_details_extraction/graph.py` with JobDetailsExtractionInput/Output schemas
  - [x] 6.3 Implement graph using `with_structured_output(TitleCompany)` and LLM (openai/gpt-4o-mini)
  - [x] 6.4 Add inline system/user prompts for extraction
  - [x] 6.5 Add error handling returning null values on failure

- [x] 7. experience_extraction Agent

  - [x] 7.1 Create `apps/agents/src/experience_extraction/__init__.py`
  - [x] 7.2 Create `apps/agents/src/experience_extraction/graph.py` with ExperienceExtractionInput/Output schemas
  - [x] 7.3 Implement `fetch_thread_messages()` using LangGraph SDK to read thread state
  - [x] 7.4 Implement graph using `with_structured_output(WorkExperienceEnhancementSuggestions)` and LLM (openai/gpt-4o)
  - [x] 7.5 Copy inline system/user prompts from existing `experience_extraction.py`
  - [x] 7.6 Add error handling with graceful degradation

- [x] 8. Frontend Dependencies & Setup

  - [x] 8.1 Install npm packages: `@assistant-ui/react`, `@assistant-ui/react-langgraph`, `@langchain/langgraph-sdk`
  - [x] 8.2 Remove shadcn-chatbot-kit if installed
  - [x] 8.3 Add environment variables to `.env.local.example`: NEXT_PUBLIC_LANGGRAPH_API_URL, NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID, LANGGRAPH_API_URL, LANGCHAIN_API_KEY

- [x] 9. resume_refinement Agent (Stateful)

  - [x] 9.1 Create `apps/agents/src/resume_refinement/__init__.py`
  - [x] 9.2 Create `apps/agents/src/resume_refinement/graph.py` with ResumeRefinementContext dataclass and ResumeRefinementState
  - [x] 9.3 Implement `propose_resume_draft` tool using `get_runtime()` for context and httpx for FastAPI calls
  - [x] 9.4 Build StateGraph with context_schema, bind tools to LLM (google/gemini-2.5-pro)
  - [x] 9.5 Load system prompt from `resume_alignment_workflow.json`
  - [x] 9.6 Add error handling for tool execution and LLM calls

- [x] 10. Frontend Integration

  - [x] 10.1 Create `apps/web/src/app/api/[...path]/route.ts` LangGraph proxy route
  - [x] 10.2 Create `apps/web/src/lib/langgraph.ts` with client-side helpers (createThread, getThreadState, sendMessage)
  - [x] 10.3 Create `apps/web/src/lib/langgraph-server.ts` with server-side helpers (runGapAnalysis, runStakeholderAnalysis, runExperienceExtraction, runJobDetailsExtraction)
  - [x] 10.4 Create `apps/web/src/components/resume-chat/ResumeChat.tsx` using useLangGraphRuntime hook
  - [x] 10.5 Update resume chat page to use ResumeChat component with thread persistence
  - [x] 10.6 Update workflow API calls to use langgraph-server.ts functions instead of FastAPI workflow endpoints

- [x] 11. Cleanup & Verification
  - [x] 11.1 Remove `apps/api/api/routes/workflows.py`
  - [x] 11.2 Remove `apps/api/api/services/job_intake_service/workflows/` directory
  - [x] 11.3 Remove old workflow API calls from frontend
