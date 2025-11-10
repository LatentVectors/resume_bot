# Overview

This sprint migrates the application from direct OpenAI/Gemini API usage to OpenRouter, which provides a unified interface for accessing multiple LLM providers through a single API. This change enables:

- Access to a wider variety of models from multiple providers
- Centralized billing and usage tracking
- Easy model switching without code changes
- Cost optimization through OpenRouter's model routing capabilities

The sprint includes:

1. Configuration updates to use OpenRouter credentials
2. CLI tooling to sync available models from OpenRouter
3. Auto-generation of model enums from OpenRouter's API
4. Refactoring all LLM calls to use OpenRouter
5. Testing and validation of the new integration

# Implementation Tasks

## Configuration

- [ ] Configure the Pydantic settings in `src/config.py` to read in the OpenRouter environment variables. Remove the existing `openai_api_key` and `gemini_api_key` fields entirely and replace with:
  - `openrouter_api_key: str` (required)
  - `openrouter_base_url: str` (default: "https://openrouter.ai/api/v1")
  - `openrouter_site_url: str | None` (optional, for app attribution)
  - `openrouter_site_name: str | None` (optional, for app attribution)
- [ ] Log attribution status once at app startup using INFO level in the `load_settings()` function in `src/config.py`. After settings are loaded, check if both `openrouter_site_url` and `openrouter_site_name` are set and log: `"OpenRouter app attribution enabled"` or `"OpenRouter app attribution disabled"`.
- [ ] See .env.example for the environment variable definitions.

## CLI Command and File Structure

- [ ] Create model sync CLI command in `src/core/models_cli.py`:

  - Follow the pattern from `src/core/prompts/cli.py`
  - Export `models_app = typer.Typer(help="Manage OpenRouter models")`
  - Implement `sync` command that:
    - Shows progress messages using rich Console
    - Calls business logic functions for fetching and generating
    - Handles errors and displays user-friendly messages
    - Returns appropriate exit codes (0 for success, 1 for failure)
  - Keep all logic in `models_cli.py` for simplicity (fetching and generation)

- [ ] Register CLI command:

  - Register `models_app` in `src/cli.py` as `models` (usage: `python cli.py models sync`)
  - Add import: `from src.core.models_cli import models_app`
  - Add line: `app.add_typer(models_app, name="models")`

- [ ] Reorganize model files:
  - Move existing `get_model()` function from `src/core/models.py` to new file `src/core/get_model.py`
  - Auto-generate `src/core/models.py` containing only the `OpenRouterModels` enum
  - Expose both `OpenRouterModels` and `get_model` in `src/core/__init__.py`

## Fetching Models from OpenRouter

- [ ] Fetch models from OpenRouter API (see https://openrouter.ai/docs/api-reference/models/get-models):

  - API endpoint: `GET https://openrouter.ai/api/v1/models`
  - Authorization: Bearer token using `OPENROUTER_API_KEY` in the `Authorization` header
  - Example: `Authorization: Bearer sk-or-...`
  - Use requests library with OpenRouter API key to GET all models from endpoint
  - Add `requests` as a dev dependency in `pyproject.toml` (CLI is only for development)
  - Fetch all models without filtering

- [ ] Expected API response structure:

  - Response is an object with a `data` key containing an array of model objects
  - Each model object contains at minimum:
    - `id`: string (e.g., "openai/gpt-4o", "anthropic/claude-3-5-sonnet")
    - `name`: string (display name, e.g., "GPT-4o")
    - `description`: string (optional, model description)

- [ ] Generate enum keys from model `id` field:

  - Use the model's `id` field (not `name`) to generate enum keys
  - Apply the following transformation rules:
    - Convert to uppercase
    - Replace forward slash `/` with double underscore `__`
    - Replace hyphens, spaces, and other special characters with single underscores `_`
    - Remove consecutive duplicate underscores
    - Prefix with `m_` if the result starts with a digit
  - Examples:
    - `"openai/gpt-4o"` → `OPENAI__GPT_4O`
    - `"anthropic/claude-3-5-sonnet"` → `ANTHROPIC__CLAUDE_3_5_SONNET`
    - `"google/gemini-pro-1.5"` → `GOOGLE__GEMINI_PRO_1_5`
  - This approach naturally organizes models by provider and avoids collisions since IDs are unique

- [ ] Use model `id` as enum value:

  - The enum value should be the original `id` string unchanged (e.g., `"openai/gpt-4o"`)
  - Include the model `name` and `description` as a docstring comment for each enum member
  - If `description` is missing, use "No description available"

- [ ] Error handling:
  - If API call fails, exit immediately with clear error message including suggestions (check API key, network connection)
  - If response is malformed (missing required `id` field), exit immediately with error
  - Do not modify existing models file if sync fails

## Generated File Structure

- [ ] Generate `src/core/models.py` with the following structure:

```python
"""This file is auto-generated. Do not manually edit."""
from __future__ import annotations

from enum import Enum


class OpenRouterModels(str, Enum):
    """Available models from OpenRouter."""

    OPENAI__GPT_4O = "openai/gpt-4o"
    """GPT-4o - Advanced reasoning model from OpenAI."""

    ANTHROPIC__CLAUDE_3_5_SONNET = "anthropic/claude-3-5-sonnet"
    """Claude 3.5 Sonnet - High-performance model from Anthropic."""

    # ... more models


ModelName = OpenRouterModels
```

- Include `from __future__ import annotations` following project standards
- Auto-generated warning comment at top: "This file is auto-generated. Do not manually edit."
- String enum class `OpenRouterModels` inheriting from `(str, Enum)`
- Each enum member format: `KEY = "id"` with docstring `"""name - description"""`
- Export `ModelName` type alias pointing to `OpenRouterModels` at the end

## Update get_model Function

- [ ] Update `get_model()` function in `src/core/get_model.py` (see https://openrouter.ai/docs/community/lang-chain):
  - Replace `init_chat_model` with direct instantiation of `ChatOpenAI` from `langchain_openai`
  - Remove existing model prefix logic and API key checking (all models go through OpenRouter)
  - Pass the following parameters to `ChatOpenAI`:
    - `api_key=settings.openrouter_api_key`
    - `base_url=settings.openrouter_base_url`
    - `model=model.value` (the model ID from enum)
    - `max_retries=max_retries`
    - `default_headers` dict containing:
      - `"HTTP-Referer": settings.openrouter_site_url` (if configured)
      - `"X-Title": settings.openrouter_site_name` (if configured)
  - Only include attribution headers if both `openrouter_site_url` and `openrouter_site_name` are set
  - Maintain singleton pattern using `_models` dict cache
  - Function signature: `get_model(model: ModelName, max_retries: int = 2) -> BaseChatModel`
  - No default model parameter (explicit model selection required)

## Refactor Existing Code

- [ ] Refactor all existing code that calls `get_model()`:

  - Every single LLM interaction must go through OpenRouter
  - `get_model()` requires an explicit model parameter with no default (no default model)

- [ ] Refactoring workflow:

  1. First, implement the CLI sync command and run `python cli.py models sync`
  2. Review the generated `src/core/models.py` enum to see available OpenRouter models
  3. For each file below, update imports and replace model selections with appropriate OpenRouter models from the generated enum

- [ ] Files to refactor (11 total):

  - `app/services/job_intake_service/workflows/gap_analysis.py`
  - `app/services/job_intake_service/workflows/stakeholder_analysis.py`
  - `app/services/job_intake_service/workflows/resume_refinement.py`
  - `src/agents/main/nodes/generate_experience.py`
  - `src/agents/main/nodes/generate_summary.py`
  - `src/agents/main/nodes/router_node.py`
  - `src/agents/main/nodes/generate_skills.py`
  - `src/features/cover_letter/llm_template.py`
  - `src/features/jobs/extraction.py`
  - `src/features/resume/cli.py`
  - `src/features/resume/llm_template.py`

- [ ] For each file:
  - Update import from `from src.core.models import OpenAIModels, get_model` to `from src.core import get_model, ModelName`
  - Replace `OpenAIModels.gpt_4o_mini` (or other enum members) with appropriate `ModelName` enum member from generated models
  - Choose appropriate OpenRouter model based on the generated enum and use case

## Testing

- [ ] Manual testing approach:
  - Set environment variables in `.env`
  - Run `python cli.py models sync` to verify model fetch and enum generation
  - Verify generated `src/core/models.py` file structure and content
  - Test a simple LLM call through `get_model()` with an OpenRouter model
  - Verify attribution headers are included when configured (inspect network requests or logs)
  - Test existing workflows that use LLMs to ensure they work with OpenRouter:
    - Job intake flow
    - Resume generation
    - Gap analysis

## Success Criteria

- [ ] All configuration changes implemented and `.env.example` updated
- [ ] `python cli.py models sync` successfully generates `src/core/models.py`
- [ ] Generated file contains valid Python enum with all OpenRouter models
- [ ] Generated file follows project standards (imports, structure, formatting)
- [ ] All 11 identified files refactored to use OpenRouter
- [ ] No references to `OpenAIModels` or old model enum remain in codebase
- [ ] Attribution logging works correctly based on configuration
- [ ] Manual testing completed: at least one successful LLM call through OpenRouter
- [ ] Existing features (job intake, resume generation, gap analysis) work without errors
- [ ] No linter errors introduced

# Reference Documentation

**OpenRouter Documentation URLs:**

- OpenRouter API Models: https://openrouter.ai/docs/api-reference/models/get-models
- OpenRouter + LangChain Integration: https://openrouter.ai/docs/community/lang-chain
- OpenRouter App Attribution: https://openrouter.ai/docs/app-attribution
- OpenRouter Quickstart: https://openrouter.ai/docs/quickstart
