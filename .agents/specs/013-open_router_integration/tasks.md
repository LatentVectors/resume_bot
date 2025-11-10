# OpenRouter Integration - Implementation Tasks

## 1. Configuration

- [x] Configure Pydantic settings in `src/config.py`
  - [x] Remove `openai_api_key` and `gemini_api_key` fields
  - [x] Add `openrouter_api_key: str` (required)
  - [x] Add `openrouter_base_url: str` (default: "https://openrouter.ai/api/v1")
  - [x] Add `openrouter_site_url: str | None` (optional)
  - [x] Add `openrouter_site_name: str | None` (optional)
  - [x] Add attribution logging in `load_settings()` function
- [x] Update `.env.example` with OpenRouter environment variables

## 2. CLI Command and File Structure

- [x] Create `src/core/models_cli.py`
  - [x] Export `models_app` typer app
  - [x] Implement `sync` command with progress messages
  - [x] Include error handling and exit codes
  - [x] Implement model fetching logic
  - [x] Implement model enum generation logic
- [x] Register CLI command in `src/cli.py`
  - [x] Add import for `models_app`
  - [x] Register with `app.add_typer()`
- [x] Reorganize model files
  - [x] Move `get_model()` to `src/core/get_model.py`
  - [x] Update `src/core/__init__.py` to expose exports
- [x] Add `requests` as dev dependency in `pyproject.toml`

## 3. Model Fetching and Generation

- [x] Implement OpenRouter API integration
  - [x] Fetch models from `https://openrouter.ai/api/v1/models`
  - [x] Use Bearer token authorization
  - [x] Parse response data array
  - [x] Handle API errors gracefully
- [x] Implement enum key generation
  - [x] Convert model `id` to uppercase
  - [x] Replace `/` with `__`
  - [x] Replace special characters with `_`
  - [x] Remove duplicate underscores
  - [x] Prefix with `m_` if starts with digit
- [x] Generate `src/core/models.py`
  - [x] Add auto-generated warning comment
  - [x] Include proper imports
  - [x] Create `OpenRouterModels` enum class
  - [x] Add docstrings for each model
  - [x] Export `ModelName` type alias

## 4. Update get_model Function

- [x] Update `src/core/get_model.py`
  - [x] Replace `init_chat_model` with `ChatOpenAI`
  - [x] Remove old model prefix logic
  - [x] Add OpenRouter configuration
  - [x] Implement attribution headers
  - [x] Maintain singleton pattern
  - [x] Update function signature

## 5. Refactor Existing Code

- [x] Run `python cli.py models sync` to generate enum
- [x] Review generated models and select appropriate ones
- [x] Refactor 11 files to use OpenRouter:
  - [x] `app/services/job_intake_service/workflows/gap_analysis.py`
  - [x] `app/services/job_intake_service/workflows/stakeholder_analysis.py`
  - [x] `app/services/job_intake_service/workflows/resume_refinement.py`
  - [x] `src/agents/main/nodes/generate_experience.py`
  - [x] `src/agents/main/nodes/generate_summary.py`
  - [x] `src/agents/main/nodes/router_node.py`
  - [x] `src/agents/main/nodes/generate_skills.py`
  - [x] `src/features/cover_letter/llm_template.py`
  - [x] `src/features/jobs/extraction.py`
  - [x] `src/features/resume/cli.py`
  - [x] `src/features/resume/llm_template.py`

## 6. Validation

- [x] Configuration changes complete
- [x] Model sync generates valid enum
- [x] All files refactored
- [x] No `OpenAIModels` references remain
- [x] Attribution logging works
- [x] No linter errors
