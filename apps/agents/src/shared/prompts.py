"""Prompt loading from local storage."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any, Final

from .prompt_names import PromptName

# ==================== Constants ====================

# Get the prompts directory (relative to this file: src/shared/prompts.py -> prompts/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent
PROMPTS_DIR: Final[Path] = _PROJECT_ROOT / "prompts"

# Re-export PromptName for backwards compatibility
__all__ = ["PromptName", "PROMPTS_DIR", "load_prompt"]


# ==================== Prompt Loading ====================


def load_prompt(name: PromptName) -> Any:
    """Load a prompt from local storage and return it as a LangChain PromptTemplate.

    Args:
        name: The PromptName enum member identifying which prompt to load

    Returns:
        The prompt object (BasePromptTemplate or RunnableSequence)

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        ValueError: If the JSON is invalid or missing required fields
        ImportError: If langchain-core is not installed
    """
    # Import LangChain dependencies
    try:
        from langchain_core.load.load import loads
        from langchain_core.prompts import BasePromptTemplate
        from langchain_core.runnables.base import RunnableSequence
    except ImportError as err:
        raise ImportError(
            "The load_prompt function requires the langchain-core "
            "package to run.\nInstall with `pip install langchain-core`"
        ) from err

    # Import warning suppressor
    try:
        from langchain_core._api import suppress_langchain_beta_warning
    except ImportError:

        @contextlib.contextmanager
        def suppress_langchain_beta_warning():  # type: ignore[misc]
            yield

    # Load prompt data from disk
    prompt_file = PROMPTS_DIR / f"{name.value}.json"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with prompt_file.open() as f:
        data = json.load(f)

    if "committed_prompt" not in data:
        raise ValueError(f"Missing 'committed_prompt' field in {prompt_file}")

    # Deserialize with LangChain's loads
    with suppress_langchain_beta_warning():
        prompt = loads(json.dumps(data["committed_prompt"]))

    # Update metadata
    if isinstance(prompt, BasePromptTemplate) or (
        isinstance(prompt, RunnableSequence) and isinstance(prompt.first, BasePromptTemplate)
    ):
        prompt_template = (
            prompt
            if isinstance(prompt, BasePromptTemplate)
            else prompt.first if isinstance(prompt.first, BasePromptTemplate) else None
        )
        if prompt_template is not None:
            if prompt_template.metadata is None:
                prompt_template.metadata = {}

            # Add metadata from our JSON
            prompt_template.metadata.update(
                {
                    "lc_hub_owner": data.get("full_name", "").split("/")[0] if "/" in data.get("full_name", "") else "",
                    "lc_hub_repo": data.get("repo_handle", ""),
                    "lc_hub_commit_hash": data.get("last_commit_hash", ""),
                }
            )

    return prompt

