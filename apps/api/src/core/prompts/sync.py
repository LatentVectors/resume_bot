"""Prompt syncing from LangSmith."""

from __future__ import annotations

import json
import re

from langchain_core.load import dumpd
from langsmith import Client

from src.config import settings
from src.logging_config import logger

from .constants import PROMPTS_DIR


def sync_prompts_from_langsmith() -> tuple[int, list[tuple[str, str]]]:
    """Sync prompts from LangSmith to local storage.

    Returns:
        Tuple of (synced_count, errors) where errors is list of (prompt_name, error_message)

    Raises:
        ValueError: If required settings are missing
        RuntimeError: If LangSmith client fails to initialize or fetch prompts
    """
    # Validate required settings
    if not settings.langsmith_api_key:
        raise ValueError("LANGSMITH_API_KEY is not configured. Please set it in your .env file.")

    if not settings.langsmith_project:
        raise ValueError("LANGSMITH_PROJECT is not configured. Please set it in your .env file.")

    # Initialize LangSmith client
    try:
        client = Client(api_key=settings.langsmith_api_key)
    except Exception as e:
        logger.exception("Failed to initialize LangSmith client")
        raise RuntimeError(f"Failed to connect to LangSmith: {e}") from e

    # Fetch prompts
    try:
        prompts_response = list(client.list_prompts(is_public=False, is_archived=False))

        # Extract the actual prompts list
        prompts = []
        for item in prompts_response:
            if isinstance(item, tuple) and item[0] == "repos":
                prompts = item[1]
                break
    except Exception as e:
        logger.exception("Failed to fetch prompts from LangSmith")
        raise RuntimeError(f"Failed to fetch prompts: {e}") from e

    if not prompts:
        return (0, [])

    # Create prompts directory
    PROMPTS_DIR.mkdir(exist_ok=True)

    synced_count = 0
    errors: list[tuple[str, str]] = []

    for prompt in prompts:
        prompt_name = "unknown"
        try:
            # Get the prompt name
            prompt_name = prompt.repo_handle if hasattr(prompt, "repo_handle") else prompt.full_name

            # Pull the latest prompt template (for model config, etc.)
            prompt_template = client.pull_prompt(prompt.repo_handle, include_model=True)

            # Pull the specific commit version to get the committed prompt content
            commit_prompt = client.pull_prompt(f"{prompt.repo_handle}:{prompt.last_commit_hash}")

            # Use LangChain's native serialization
            committed_prompt_content = dumpd(commit_prompt)

            # Extract the data to save
            prompt_data = {
                "id": str(prompt.id),
                "name": prompt_name,
                "repo_handle": prompt.repo_handle,
                "full_name": prompt.full_name,
                "description": prompt.description,
                "readme": prompt.readme,
                "tags": prompt.tags,
                "created_at": prompt.created_at.isoformat(),
                "updated_at": prompt.updated_at.isoformat(),
                "is_public": prompt.is_public,
                "is_archived": prompt.is_archived,
                "num_likes": prompt.num_likes,
                "num_downloads": prompt.num_downloads,
                "num_views": prompt.num_views,
                "last_commit_hash": prompt.last_commit_hash,
                "num_commits": prompt.num_commits,
                "prompt_template": dumpd(prompt_template),
                "committed_prompt": committed_prompt_content,
            }

            # Sanitize filename and save
            filename = sanitize_filename(prompt_name)
            output_path = PROMPTS_DIR / f"{filename}.json"

            with output_path.open("w", encoding="utf-8") as f:
                json.dump(prompt_data, f, indent=2, ensure_ascii=False, default=str)

            synced_count += 1

        except Exception as e:
            logger.error(f"Failed to sync prompt '{prompt_name}'", exc_info=True)
            errors.append((prompt_name, str(e)))

    return (synced_count, errors)


def sanitize_filename(name: str) -> str:
    """Sanitize a prompt name for use as a filename.

    Args:
        name: The prompt name to sanitize

    Returns:
        A sanitized filename safe for filesystem use
    """
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[/\\:*?"<>|]', "_", name)
    # Remove any leading/trailing whitespace or dots
    sanitized = sanitized.strip(". ")
    # Replace multiple underscores with single underscore
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized

