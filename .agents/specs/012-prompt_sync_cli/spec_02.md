This extends spec_01.md, which has been implemented.

## Overview

Create a prompt loading module at `src/core/prompts/` that provides type-safe prompt loading from the local `/prompts` directory. This module will include:

- An auto-generated enum of prompt names for type safety
- A loader function that deserializes saved prompts into LangChain objects
- Integration with the existing `langsmith prompts sync` CLI command

## Module Structure

**New Package: `src/core/prompts/`**

Create a new package with the following structure:

- `src/core/prompts/__init__.py` - Main exports (loader function, enum)
- `src/core/prompts/names.py` - Auto-generated enum of prompt names (DO NOT EDIT MANUALLY)
- `src/core/prompts/loader.py` - Prompt loading implementation
- `src/core/prompts/sync.py` - Prompt syncing business logic
- `src/core/prompts/enum_generator.py` - Enum generation logic
- `src/core/prompts/cli.py` - CLI interface for prompt operations (replaces `cli_langsmith.py`)

**Architecture Principle**: All prompt-related functionality (business logic + CLI interface) is consolidated in `src/core/prompts/`. The root `cli.py` simply imports and registers the prompts CLI subcommand group.

## Prompt Loader Function

We need a function that can load a prompt from the `/prompts` directory. It should closely mirror the `pull_prompt` method defined by the LangSmith library, adapted to read from local disk instead of the LangSmith API.

**Reference: LangSmith `pull_prompt` Implementation**

Here is the actual implementation from the LangSmith client that we should follow:

```python
def pull_prompt(
    self, prompt_identifier: str, *, include_model: Optional[bool] = False
) -> Any:
    """Pull a prompt and return it as a LangChain PromptTemplate.

    This method requires `langchain-core <https://pypi.org/project/langchain-core/>`__.

    Args:
        prompt_identifier (str): The identifier of the prompt.
        include_model (Optional[bool], default=False): Whether to include the model information in the prompt data.

    Returns:
        Any: The prompt object in the specified format.
    """
    try:
        from langchain_core.language_models.base import BaseLanguageModel
        from langchain_core.load.load import loads
        from langchain_core.output_parsers import BaseOutputParser
        from langchain_core.prompts import BasePromptTemplate
        from langchain_core.prompts.structured import StructuredPrompt
        from langchain_core.runnables.base import RunnableBinding, RunnableSequence
    except ImportError:
        raise ImportError(
            "The client.pull_prompt function requires the langchain-core"
            "package to run.\nInstall with `pip install langchain-core`"
        )
    try:
        from langchain_core._api import suppress_langchain_beta_warning
    except ImportError:

        @contextlib.contextmanager
        def suppress_langchain_beta_warning():
            yield

    prompt_object = self.pull_prompt_commit(
        prompt_identifier, include_model=include_model
    )
    with suppress_langchain_beta_warning():
        prompt = loads(json.dumps(prompt_object.manifest))

    if (
        isinstance(prompt, BasePromptTemplate)
        or isinstance(prompt, RunnableSequence)
        and isinstance(prompt.first, BasePromptTemplate)
    ):
        prompt_template = (
            prompt
            if isinstance(prompt, BasePromptTemplate)
            else (
                prompt.first
                if isinstance(prompt, RunnableSequence)
                and isinstance(prompt.first, BasePromptTemplate)
                else None
            )
        )
        if prompt_template is None:
            raise ls_utils.LangSmithError(
                "Prompt object is not a valid prompt template."
            )

        if prompt_template.metadata is None:
            prompt_template.metadata = {}
        prompt_template.metadata.update(
            {
                "lc_hub_owner": prompt_object.owner,
                "lc_hub_repo": prompt_object.repo,
                "lc_hub_commit_hash": prompt_object.commit_hash,
            }
        )

    # Transform 2-step RunnableSequence to 3-step for structured prompts
    # See create_commit for the reverse transformation
    if (
        include_model
        and isinstance(prompt, RunnableSequence)
        and isinstance(prompt.first, StructuredPrompt)
        # Make forward-compatible in case we let update the response type
        and (
            len(prompt.steps) == 2 and not isinstance(prompt.last, BaseOutputParser)
        )
    ):
        if isinstance(prompt.last, RunnableBinding) and isinstance(
            prompt.last.bound, BaseLanguageModel
        ):
            seq = cast(RunnableSequence, prompt.first | prompt.last.bound)
            if len(seq.steps) == 3:  # prompt | bound llm | output parser
                rebound_llm = seq.steps[1]
                prompt = RunnableSequence(
                    prompt.first,
                    rebound_llm.bind(**{**prompt.last.kwargs}),
                    seq.last,
                )
            else:
                prompt = seq  # Not sure

        elif isinstance(prompt.last, BaseLanguageModel):
            prompt: RunnableSequence = prompt.first | prompt.last  # type: ignore[no-redef, assignment]
        else:
            pass

    return prompt
```

**Key Implementation Notes:**

- The LangSmith version calls `self.pull_prompt_commit()` to get the prompt object, then deserializes `prompt_object.manifest` with `loads(json.dumps(...))`
- Our version will read from disk and deserialize the stored JSON data the same way
- Follow the exact same metadata updating and prompt transformation logic
- Use the same warning suppression pattern

## Function Signature and Return Type

The `pull_prompt` function uses the client to pull the prompt from the LangSmith server. Our function will read from disk. Unlike `pull_prompt` which returns `Any`, we use specific type hints for clarity.

**Function Signature (in `src/core/prompts/loader.py`):**

```python
def load_prompt(name: PromptName) -> BasePromptTemplate | RunnableSequence:
    """Load a prompt from local storage by its enum name.

    Args:
        name: The PromptName enum member identifying which prompt to load

    Returns:
        The deserialized LangChain prompt object (either BasePromptTemplate or RunnableSequence)

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        ValueError: If the JSON is invalid or missing required fields
        RuntimeError: If deserialization fails
    """
```

**Import statements needed:**

```python
from langchain_core.prompts import BasePromptTemplate
from langchain_core.runnables.base import RunnableSequence
from langchain_core.load import loads
```

**Return Type**: `BasePromptTemplate | RunnableSequence` - These are the actual types returned by LangChain's `loads()` deserialization, matching what `pull_prompt` produces.

## Auto-Generated Enum

**File: `src/core/prompts/names.py`**

- Auto-generated file containing a `PromptName` enum
- Enum values use the prompt filename (without `.json` extension) as both the member name and value
- Example: `GAP_ANALYSIS = "gap_analysis"`
- Include header comment: `# AUTO-GENERATED FILE - DO NOT EDIT MANUALLY`
- Include generation timestamp and instructions to run sync command to update
- Generated by scanning `/prompts` directory after sync completes

**Enum Generation:**

- Integrated into the `prompts sync` CLI command (in `src/core/prompts/cli.py`)
- Runs automatically after successful prompt sync
- Always overwrites `src/core/prompts/names.py` completely
- Converts prompt filenames to valid Python enum member names (uppercase, underscores)

**Example generated enum:**

```python
# AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
# Generated by: prompts sync
# Last updated: 2025-11-06T10:30:00Z
# To update: run `python cli.py prompts sync`

from enum import Enum

class PromptName(Enum):
    """Enum of available prompts in the /prompts directory."""

    EXTRACT_EXPERIENCE_UPDATES = "extract_experience_updates"
    GAP_ANALYSIS = "gap_analysis"
    RESUME_ALIGNMENT_WORKFLOW = "resume_alignment_workflow"
    STAKEHOLDER_ANALYSIS = "stakeholder_analysis"
```

## Prompt Data Source

The synced JSON files contain a `prompt_template` field that mirrors the `manifest` data from LangSmith's prompt objects. Our `load_prompt` function should:

- Read the `prompt_template` field from the JSON file (equivalent to `prompt_object.manifest` in LangSmith)
- Deserialize it using `loads(json.dumps(prompt_template))` exactly like `pull_prompt` does
- Apply the same metadata updates and transformations as LangSmith's implementation

## Implementation Details

### Loader Function Implementation (`src/core/prompts/loader.py`)

The implementation should mirror LangSmith's `pull_prompt` as closely as possible:

**Implementation (following LangSmith's pattern exactly):**

```python
from __future__ import annotations

import contextlib
import json
from pathlib import Path
from typing import Any, Final, cast

from .names import PromptName

PROMPTS_DIR: Final[Path] = Path("prompts")


def load_prompt(name: PromptName, *, include_model: bool = False) -> Any:
    """Load a prompt from local storage and return it as a LangChain PromptTemplate.

    This function mirrors the LangSmith Client.pull_prompt() implementation,
    adapted to read from local disk instead of the LangSmith API.

    Args:
        name: The PromptName enum member identifying which prompt to load
        include_model: Whether to include model information in the prompt data (currently unused, for future compatibility)

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
    except ImportError:
        raise ImportError(
            "The load_prompt function requires the langchain-core "
            "package to run.\nInstall with `pip install langchain-core`"
        )

    # Import warning suppressor (same as pull_prompt)
    try:
        from langchain_core._api import suppress_langchain_beta_warning
    except ImportError:
        @contextlib.contextmanager
        def suppress_langchain_beta_warning():  # type: ignore
            yield

    # Load prompt data from disk (replaces pull_prompt_commit call)
    prompt_file = PROMPTS_DIR / f"{name.value}.json"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")

    with prompt_file.open() as f:
        data = json.load(f)

    # Extract prompt_template (equivalent to prompt_object.manifest)
    if "prompt_template" not in data:
        raise ValueError(f"Missing 'prompt_template' field in {prompt_file}")

    manifest = data["prompt_template"]

    # Deserialize with LangChain's loads (same as pull_prompt)
    with suppress_langchain_beta_warning():
        prompt = loads(json.dumps(manifest))

    # Update metadata (same logic as pull_prompt, adapted for our data structure)
    if (
        isinstance(prompt, BasePromptTemplate)
        or isinstance(prompt, RunnableSequence)
        and isinstance(prompt.first, BasePromptTemplate)
    ):
        prompt_template = (
            prompt
            if isinstance(prompt, BasePromptTemplate)
            else (
                prompt.first
                if isinstance(prompt, RunnableSequence)
                and isinstance(prompt.first, BasePromptTemplate)
                else None
            )
        )
        if prompt_template is None:
            raise RuntimeError(
                "Prompt object is not a valid prompt template."
            )

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
        and (
            len(prompt.steps) == 2 and not isinstance(prompt.last, BaseOutputParser)
        )
    ):
        if isinstance(prompt.last, RunnableBinding) and isinstance(
            prompt.last.bound, BaseLanguageModel
        ):
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
            prompt: RunnableSequence = prompt.first | prompt.last  # type: ignore[no-redef, assignment]
        else:
            pass

    return prompt
```

### Module Exports (`src/core/prompts/__init__.py`)

Export the loader function and enum for easy access:

```python
"""Prompt loading and management."""

from .loader import load_prompt
from .names import PromptName

__all__ = ["load_prompt", "PromptName"]
```

### Enum Generator (`src/core/prompts/enum_generator.py`)

**Separate module for enum generation logic:**

```python
"""Enum generation for prompt names."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Final

PROMPTS_DIR: Final[Path] = Path("prompts")


def generate_prompt_enum() -> int:
    """Generate the PromptName enum from files in the prompts directory.

    Returns:
        Number of prompt enum members generated
    """
    # Scan prompts directory
    prompt_files = sorted(PROMPTS_DIR.glob("*.json"))

    # Generate enum members (create empty enum if no prompts found)
    enum_members = []
    for prompt_file in prompt_files:
        # Convert filename to enum member name (uppercase with underscores)
        name = prompt_file.stem  # Remove .json extension
        enum_name = name.upper()
        enum_members.append(f'    {enum_name} = "{name}"')

    # Generate enum file content
    timestamp = datetime.now().isoformat()

    if enum_members:
        enum_body = "\n".join(enum_members)
    else:
        # Create empty enum with a pass statement
        enum_body = "    pass"

    enum_content = f'''# AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
# Generated by: prompts sync
# Last updated: {timestamp}
# To update: run `python cli.py prompts sync`

from enum import Enum


class PromptName(Enum):
    """Enum of available prompts in the /prompts directory."""

{enum_body}
'''

    # Write to file
    enum_file = Path("src/core/prompts/names.py")
    enum_file.parent.mkdir(parents=True, exist_ok=True)
    enum_file.write_text(enum_content, encoding="utf-8")

    return len(enum_members)
```

### Sync Module (`src/core/prompts/sync.py`)

**Move sync logic from `cli_langsmith.py` to dedicated module:**

```python
"""Prompt syncing from LangSmith."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from langchain_core.load import dumpd
from langsmith import Client

from src.config import settings
from src.logging_config import logger

PROMPTS_DIR: Final[Path] = Path("prompts")


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
            from .sync import sanitize_filename  # Import from same module
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
    import re

    # Replace invalid characters with underscores
    sanitized = re.sub(r'[/\\:*?"<>|]', "_", name)
    # Remove any leading/trailing whitespace or dots
    sanitized = sanitized.strip(". ")
    # Replace multiple underscores with single underscore
    sanitized = re.sub(r"_+", "_", sanitized)
    return sanitized
```

### CLI Interface (`src/core/prompts/cli.py`)

**CLI interface for prompt operations:**

This module provides the Typer CLI interface for prompt management, replacing the old `src/cli_langsmith.py`:

```python
"""CLI interface for prompt operations."""

from __future__ import annotations

import typer
from rich.console import Console

from .enum_generator import generate_prompt_enum
from .sync import sync_prompts_from_langsmith

# Create the prompts CLI app
prompts_app = typer.Typer(help="Manage prompts from LangSmith")

# Console for rich output
console = Console()


@prompts_app.command("sync")
def sync_prompts_command(
    fail_fast: bool = typer.Option(
        True,
        "--fail-fast/--no-fail-fast",
        help="Exit immediately on first error (default: True)",
    ),
) -> None:
    """Sync prompts from LangSmith to local storage."""
    from src.logging_config import logger

    console.print("Connecting to LangSmith...", style="cyan")

    try:
        # Call business logic
        synced_count, errors = sync_prompts_from_langsmith()

        if not errors:
            console.print(f"Syncing prompts to /prompts/...", style="cyan")
            console.print(f"[bold green]Successfully synced {synced_count} prompts[/bold green]")

            # Generate enum
            console.print("Generating PromptName enum...", style="cyan")
            enum_count = generate_prompt_enum()
            console.print(
                f"Generated enum with {enum_count} prompts at [bold]src/core/prompts/names.py[/bold]",
                style="green"
            )
        else:
            # Handle errors based on fail_fast
            if fail_fast and errors:
                prompt_name, error = errors[0]
                console.print(f"[bold red]Error:[/bold red] Failed to sync prompt '{prompt_name}': {error}")
                raise typer.Exit(1)
            else:
                console.print(f"[yellow]Synced {synced_count}/{synced_count + len(errors)} prompts ({len(errors)} failed)[/yellow]")
                console.print("\n[bold]Failed prompts:[/bold]")
                for prompt_name, error in errors:
                    console.print(f"  - {prompt_name}: {error}", style="red")
                raise typer.Exit(1)

    except (ValueError, RuntimeError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.exception("Failed to sync prompts")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    prompts_app()
```

### Root CLI Integration (`cli.py` or `src/cli.py`)

**Import and register the prompts CLI:**

The root CLI should import the `prompts_app` from `src.core.prompts.cli` and register it:

```python
"""Root CLI aggregator."""

from __future__ import annotations

import typer

from src.core.prompts.cli import prompts_app

# Create main CLI app
app = typer.Typer(help="Resume application CLI")

# Register prompts subcommand
app.add_typer(prompts_app, name="prompts")

if __name__ == "__main__":
    app()
```

**Command invocation:**

```bash
python cli.py prompts sync
```

## Files to Create

1. **`src/core/prompts/__init__.py`** - Package initialization and exports
2. **`src/core/prompts/loader.py`** - Prompt loader implementation
3. **`src/core/prompts/names.py`** - Auto-generated enum (will be created by sync command)
4. **`src/core/prompts/sync.py`** - Prompt syncing business logic
5. **`src/core/prompts/enum_generator.py`** - Enum generation logic
6. **`src/core/prompts/cli.py`** - CLI interface for prompt operations

## Files to Modify

1. **`cli.py`** (or **`src/cli.py`**) - Import and register prompts CLI subcommand

## Files to Delete

1. **`src/cli_langsmith.py`** - Replaced by `src/core/prompts/cli.py`

## Usage Example

After implementation, prompts can be loaded with type safety:

```python
from src.core.prompts import load_prompt, PromptName

# Load a prompt with type-safe enum
prompt = load_prompt(PromptName.GAP_ANALYSIS)

# Use with LangChain
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")
chain = prompt | llm
result = chain.invoke({"job_description": "...", "work_experience": "..."})
```

## Technical Requirements

- Use Python 3.12 type annotations throughout
- Follow existing code style (see `.cursor/rules/standards/code_style/python`)
- Use `pathlib.Path` for all file operations
- Include proper docstrings (Google-style)
- Use standard Python exceptions (`FileNotFoundError`, `ValueError`, `RuntimeError`)
- Log errors with proper context using the project logger
- Use `typing.Final` for the PROMPTS_DIR constant

## Dependencies

No new dependencies required. Uses existing packages:

- `langchain-core` (already required by spec_01)
- Standard library: `json`, `pathlib`, `contextlib`, `enum`, `datetime`

## Testing and Verification

### Manual Testing Steps

1. **Sync prompts from LangSmith:**

   ```bash
   python cli.py langsmith prompts sync
   ```

   - Verify prompts are saved to `/prompts/` directory
   - Verify `src/core/prompts/names.py` is created with correct enum members
   - Check that timestamp and header comments are present in generated enum

2. **Test prompt loading:**

   ```python
   from src.core.prompts import load_prompt, PromptName

   # Test loading each prompt
   for prompt_name in PromptName:
       prompt = load_prompt(prompt_name)
       print(f"✓ Loaded {prompt_name.value}: {type(prompt).__name__}")
   ```

3. **Test with LangChain:**

   ```python
   from src.core.prompts import load_prompt, PromptName
   from langchain_openai import ChatOpenAI

   prompt = load_prompt(PromptName.GAP_ANALYSIS)
   llm = ChatOpenAI(model="gpt-4", temperature=0)
   chain = prompt | llm

   # Test with sample inputs (verify input_variables match)
   result = chain.invoke({
       "job_description": "Sample job description",
       "work_experience": "Sample work experience"
   })
   print(f"✓ Chain execution successful: {len(result.content)} chars")
   ```

4. **Test error handling:**
   - Manually delete a prompt file and verify `FileNotFoundError` is raised
   - Corrupt a JSON file and verify `ValueError` is raised appropriately

### Automated Test Suggestions

Create `tests/test_prompt_loading.py`:

- Test that all enum members correspond to actual files
- Test loading each prompt returns correct type
- Test error cases (missing file, invalid JSON)
- Test that prompt has expected attributes (input_variables, etc.)

## Success Criteria

- [ ] `src/core/prompts/` package created with `__init__.py`, `loader.py`, `names.py`
- [ ] `load_prompt()` function successfully loads and deserializes prompts
- [ ] `PromptName` enum auto-generated with all prompt files
- [ ] Enum generation integrated into `langsmith prompts sync` command
- [ ] Type hints are specific (`BasePromptTemplate | RunnableSequence`)
- [ ] Standard exceptions used for error handling
- [ ] Code follows project standards (Python 3.12, Google docstrings, pathlib)
- [ ] Manual testing confirms prompts can be loaded and used with LangChain
- [ ] Enum file has appropriate header comments warning against manual edits

## Edge Cases and Considerations

1. **Empty prompts directory**: Create empty enum with `pass` statement (no members)
2. **Invalid prompt filenames**: Sanitize filenames to valid Python identifiers (replace hyphens with underscores, etc.)
3. **Circular imports**: Loader imports enum from `names.py`, but enum is standalone (no imports from loader)
4. **Missing prompt_template field**: Handle gracefully with clear error message pointing to possible sync issue
5. **LangChain version compatibility**: The `suppress_langchain_beta_warning` fallback ensures compatibility across versions
6. **Module organization**: All prompt functionality (business logic + CLI) lives in `src/core/prompts/` module
7. **CLI integration**: Root CLI simply imports and registers the `prompts_app` from `src.core.prompts.cli`

## Relationship to Previous Work

This spec extends **spec_01.md** which implemented:

- Initial CLI structure for LangSmith operations (`src/cli_langsmith.py`)
- LangSmith client integration
- JSON prompt storage in `/prompts` directory
- Prompt syncing with full metadata and `prompt_template`/`committed_prompt` fields

This spec adds:

- Type-safe prompt loading via `load_prompt()` function
- Auto-generated `PromptName` enum for compile-time safety
- Integration with existing LangChain deserialization
- Developer-friendly API for using synced prompts
- Reorganization: All prompt functionality consolidated in `src/core/prompts/` module
- Deletion of `src/cli_langsmith.py` in favor of `src/core/prompts/cli.py`

## Rationale and Design Decisions

**Why `src/core/prompts/` package?**

- Prompts are core system functionality used across features
- Package structure allows logical grouping (loader, enum, potential future utilities)
- Aligns with existing `src/core/` organization

**Why auto-generate enum?**

- Eliminates manual sync between filesystem and code
- Provides IDE autocomplete and type checking
- Prevents typos in prompt names
- Always reflects actual available prompts

**Why use `prompt_template` field?**

- Mirrors LangSmith's `pull_prompt` behavior which deserializes `prompt_object.manifest`
- Follows LangSmith's implementation as closely as possible
- The `prompt_template` field is equivalent to the manifest data from LangSmith

**Why `BasePromptTemplate | RunnableSequence` return type?**

- Accurately reflects LangChain's deserialization output
- More specific than `Any`, enabling better type checking
- Matches actual types developers will work with

**Why standard exceptions instead of custom?**

- Simpler implementation (KISS principle)
- Standard exceptions are well-understood
- No need for custom exception hierarchy for this use case

**Why overwrite enum on every sync?**

- Simplest approach (no merge logic needed)
- Enum is purely derived data (can always be regenerated)
- Clear warning comments prevent manual edits
- Ensures enum always matches filesystem state

**Why consolidate all prompt functionality in `src/core/prompts/`?**

- Single module contains all prompt-related code (business logic + CLI interface)
- Easy to find and understand all prompt functionality
- Eliminates need for separate `cli_langsmith.py` file
- Follows domain-driven organization (prompts as a cohesive domain)
- Root CLI becomes a simple aggregator of domain modules
- Separation within module: `sync.py`/`enum_generator.py` (business logic) separate from `cli.py` (interface)

**Why mirror LangSmith's `pull_prompt` exactly?**

- Leverage battle-tested implementation
- Ensures compatibility with LangChain ecosystem
- Reduces risk of introducing bugs
- Makes codebase easier to understand for developers familiar with LangSmith
- Only adapt what's necessary (API calls → disk reads)
