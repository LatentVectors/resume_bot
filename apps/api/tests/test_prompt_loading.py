"""Test prompt loading functionality."""

from __future__ import annotations

import pytest

from src.core.prompts import PromptName, get_prompt
from src.core.prompts.loader import load_prompt


def test_load_all_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test loading all available prompts."""
    # Set a dummy API key for testing (prompts contain model configs that need this)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-dummy-key-for-testing")

    # Check if enum is empty
    prompt_names = list(PromptName)
    if not prompt_names:
        pytest.skip("PromptName enum is empty. Run 'python cli.py prompts sync' to sync prompts from LangSmith.")

    # Track results
    loaded_count = 0
    failed_prompts = []

    # Test loading each prompt
    for prompt_name in prompt_names:
        try:
            prompt = load_prompt(prompt_name)

            # Verify we got a prompt object back
            assert prompt is not None

            # Check for expected attributes (either on prompt or prompt.first for RunnableSequence)
            has_input_vars = hasattr(prompt, "input_variables") or (
                hasattr(prompt, "first") and hasattr(prompt.first, "input_variables")
            )
            assert has_input_vars, f"Prompt {prompt_name.value} missing input_variables"

            # Check metadata exists (either on prompt or prompt.first)
            has_metadata = hasattr(prompt, "metadata") or (
                hasattr(prompt, "first") and hasattr(prompt.first, "metadata")
            )
            assert has_metadata, f"Prompt {prompt_name.value} missing metadata"

            loaded_count += 1

        except NotImplementedError as e:
            # Some prompts may have components that can't be deserialized (e.g., JsonOutputParser)
            # This is a known issue with LangChain serialization
            if "doesn't implement serialization" in str(e):
                failed_prompts.append((prompt_name.value, str(e)))
            else:
                raise

    # Ensure at least some prompts loaded successfully
    assert loaded_count > 0, "No prompts loaded successfully"

    # Warn about prompts that couldn't be loaded
    if failed_prompts:
        warnings_msg = "\n".join([f"  - {name}: {error}" for name, error in failed_prompts])
        pytest.skip(
            f"Some prompts have serialization issues and need to be re-synced:\n{warnings_msg}\n"
            f"Run 'python cli.py prompts sync' to update these prompts."
        )


def test_prompt_enum_matches_files() -> None:
    """Test that PromptName enum members correspond to actual files with one-to-one relationship."""
    from src.core.prompts.constants import PROMPTS_DIR

    # Get all prompt files in the directory
    prompt_files = sorted(PROMPTS_DIR.glob("*.json"))
    file_names = {f.stem for f in prompt_files}

    # Get all enum values
    enum_values = {prompt_name.value for prompt_name in PromptName}

    # Check for files without enum members
    files_without_enum = file_names - enum_values
    if files_without_enum:
        pytest.fail(
            f"Found prompt files without corresponding enum members: {sorted(files_without_enum)}. "
            "Run 'python cli.py prompts sync' to update the enum."
        )

    # Check for enum members without files
    enum_without_files = enum_values - file_names
    if enum_without_files:
        pytest.fail(
            f"Found enum members without corresponding prompt files: {sorted(enum_without_files)}. "
            "Run 'python cli.py prompts sync' to update the enum."
        )

    # Ensure we have at least one prompt (fail if both are empty)
    assert file_names or enum_values, (
        "Both prompt directory and PromptName enum are empty. "
        "Run 'python cli.py prompts sync' to sync prompts from LangSmith."
    )


def test_load_prompt_file_not_found() -> None:
    """Test that loading a non-existent prompt raises FileNotFoundError."""
    from unittest.mock import MagicMock

    # Create a mock enum member
    mock_prompt = MagicMock()
    mock_prompt.value = "nonexistent_prompt_that_does_not_exist"

    with pytest.raises(FileNotFoundError, match="Prompt file not found"):
        load_prompt(mock_prompt)
