"""Prompt loading from local storage."""

from __future__ import annotations

import contextlib
import json
from enum import Enum
from pathlib import Path
from typing import Any, Final, cast


# ==================== Constants ====================

# Get the prompts directory (relative to this file: src/shared/prompts.py -> prompts/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR: Final[Path] = _PROJECT_ROOT / "prompts"


# ==================== Prompt Names Enum ====================


class PromptName(Enum):
    """Enum of available prompts in the /prompts directory."""

    EXTRACT_EXPERIENCE_UPDATES = "extract_experience_updates"
    GAP_ANALYSIS = "gap_analysis"
    RESUME_ALIGNMENT_WORKFLOW = "resume_alignment_workflow"
    STAKEHOLDER_ANALYSIS = "stakeholder_analysis"


# ==================== Prompt Loading ====================


def load_prompt(name: PromptName, *, include_model: bool = False) -> Any:
    """Load a prompt from local storage and return it as a LangChain PromptTemplate.

    This function mirrors the LangSmith Client.pull_prompt() implementation,
    adapted to read from local disk instead of the LangSmith API.

    Args:
        name: The PromptName enum member identifying which prompt to load
        include_model: Whether to include model information in the prompt data

    Returns:
        The prompt object (BasePromptTemplate or RunnableSequence)

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        ValueError: If the JSON is invalid or missing required fields
        ImportError: If langchain-core is not installed
    """
    # Import LangChain dependencies (same as pull_prompt)
    try:
        from langchain_core.language_models.base import BaseLanguageModel
        from langchain_core.load.load import loads
        from langchain_core.output_parsers import BaseOutputParser
        from langchain_core.prompts import BasePromptTemplate
        from langchain_core.prompts.structured import StructuredPrompt
        from langchain_core.runnables.base import RunnableBinding, RunnableSequence
    except ImportError as err:
        raise ImportError(
            "The load_prompt function requires the langchain-core "
            "package to run.\nInstall with `pip install langchain-core`"
        ) from err

    # Import warning suppressor (same as pull_prompt)
    try:
        from langchain_core._api import suppress_langchain_beta_warning
    except ImportError:

        @contextlib.contextmanager
        def suppress_langchain_beta_warning():  # type: ignore[misc]
            yield

    # Load prompt data from disk (replaces pull_prompt_commit call)
    prompt_file = PROMPTS_DIR / f"{name.value}.json"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with prompt_file.open() as f:
        data = json.load(f)

    # Extract the appropriate manifest based on include_model
    # When include_model=False (default), use committed_prompt (without model/parser)
    # When include_model=True, use prompt_template (with model/parser)
    if include_model:
        if "prompt_template" not in data:
            raise ValueError(f"Missing 'prompt_template' field in {prompt_file}")
        manifest = data["prompt_template"]
    else:
        if "committed_prompt" not in data:
            raise ValueError(f"Missing 'committed_prompt' field in {prompt_file}")
        manifest = data["committed_prompt"]

    # Deserialize with LangChain's loads (same as pull_prompt)
    with suppress_langchain_beta_warning():
        prompt = loads(json.dumps(manifest))

    # Update metadata (same logic as pull_prompt, adapted for our data structure)
    if isinstance(prompt, BasePromptTemplate) or (
        isinstance(prompt, RunnableSequence) and isinstance(prompt.first, BasePromptTemplate)
    ):
        prompt_template = (
            prompt
            if isinstance(prompt, BasePromptTemplate)
            else (
                prompt.first
                if isinstance(prompt, RunnableSequence) and isinstance(prompt.first, BasePromptTemplate)
                else None
            )
        )
        if prompt_template is None:
            raise RuntimeError("Prompt object is not a valid prompt template.")

        if prompt_template.metadata is None:
            prompt_template.metadata = {}

        # Add metadata from our JSON (adapt owner/repo/commit_hash from our data structure)
        prompt_template.metadata.update(
            {
                "lc_hub_owner": data.get("full_name", "").split("/")[0] if "/" in data.get("full_name", "") else "",
                "lc_hub_repo": data.get("repo_handle", ""),
                "lc_hub_commit_hash": data.get("last_commit_hash", ""),
            }
        )

    # Transform 2-step RunnableSequence to 3-step for structured prompts
    # (Same logic as pull_prompt - only relevant if include_model becomes used)
    if (
        include_model
        and isinstance(prompt, RunnableSequence)
        and isinstance(prompt.first, StructuredPrompt)
        and (len(prompt.steps) == 2 and not isinstance(prompt.last, BaseOutputParser))
    ):
        if isinstance(prompt.last, RunnableBinding) and isinstance(prompt.last.bound, BaseLanguageModel):
            seq = cast(RunnableSequence, prompt.first | prompt.last.bound)
            if len(seq.steps) == 3:  # prompt | bound llm | output parser
                rebound_llm = seq.steps[1]
                prompt = RunnableSequence(
                    prompt.first,
                    rebound_llm.bind(**{**prompt.last.kwargs}),
                    seq.last,
                )
            else:
                prompt = seq

        elif isinstance(prompt.last, BaseLanguageModel):
            prompt = prompt.first | prompt.last
        else:
            pass

    return prompt

