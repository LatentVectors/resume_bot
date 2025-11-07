## Overview

Create a CLI command for syncing prompts from LangSmith to local storage. This CLI will be extensible for future LangSmith operations beyond prompts.

## Command Structure

- Main command group: `langsmith`
- Initial subcommand: `prompts sync`
- Full command: `python cli.py langsmith prompts sync`
- Uses Typer for CLI framework
- Uses rich library for colorized console output (no emojis)

## File Structure

**New Files to Create:**

- `cli.py` - Root entrypoint that imports and exposes the CLI app
- `src/cli.py` - Root CLI aggregator that imports and attaches subcommand groups
- `src/cli_langsmith.py` - LangSmith operations CLI module

**Files to Modify:**

- `pyproject.toml` - Add `langsmith>=0.1.0` to dependencies

**Settings (no changes needed):**

- Use existing `langsmith_api_key` and `langsmith_project` fields in `src/config.py` Settings class
- Read via Pydantic Settings from `.env` file

## Prompts Storage

- **Directory**: `/prompts` (root level)
- **Format**: JSON files, one per prompt
- **Filename**: Sanitized prompt name from LangSmith (use any reasonable sanitization for filesystem compatibility)
- **Overwrite behavior**: Always overwrite existing files
- **JSON structure**: TBD - will be determined by exploring LangSmith API response during implementation. Must include:
  - Prompt content/text
  - Model information (name, provider, parameters)
  - Any other metadata returned by the API

## LangSmith Client Integration

- **Package**: `langsmith` Python package
- **Client initialization**: `from langsmith import Client; client = Client()`
- **Authentication**: Client reads `LANGSMITH_API_KEY` from environment (via Settings)
- **API Methods** (from [LangSmith Client documentation](https://reference.langchain.com/python/langsmith/observability/sdk/client/)):
  - **`list_prompts()`**: Lists all prompts with pagination support
    - Supports filtering parameters: `is_public`, `is_archived`, `query`
    - Pagination: `limit`, `offset` parameters
    - Returns an iterator of prompt objects
  - **`pull_prompt(owner_name, prompt_name, ...)`**: Pulls a specific prompt with full details
    - Supports `include_model` parameter to include model configuration
    - Returns prompt content and metadata
  - **`get_prompt(prompt_identifier)`**: Gets a specific prompt by identifier
    - Returns prompt details including content and metadata

### Implementation Approach

1. Initialize LangSmith client: `client = Client()`
2. Call `client.list_prompts()` to get all prompts from the workspace
   - Consider pagination if there are many prompts (use `limit` parameter)
3. For each prompt in the list:
   - Extract prompt identifier/name from the prompt object
   - Optionally call `client.get_prompt(prompt_identifier)` to fetch full details if needed
   - Extract prompt content and model information from the response
   - Sanitize the prompt name for use as a filename
   - Serialize to JSON and save to `/prompts/{sanitized_name}.json`
4. The exact response structure (fields, nesting) will be determined during implementation by inspecting the actual API responses

**Note**: The `pull_prompt()` method appears designed for the LangChain Hub format (owner/repo style) and may require different parameters than simply syncing workspace prompts. The implementation should validate which method best suits retrieving all workspace prompts with their model configurations.

### Example Code Structure

```python
from langsmith import Client
from pathlib import Path
import json

client = Client()

# List all prompts
prompts = client.list_prompts()

# Create output directory
output_dir = Path("prompts")
output_dir.mkdir(exist_ok=True)

# Process each prompt
for prompt in prompts:
    # Get full prompt details if needed
    # prompt_details = client.get_prompt(prompt.id)

    # Extract data and save
    prompt_data = {
        "name": prompt.name,
        "prompt": prompt.content,  # Actual field names TBD
        "model": prompt.model_config,  # Actual field names TBD
        # ... other fields
    }

    # Sanitize filename and save
    filename = sanitize_filename(prompt.name)
    output_path = output_dir / f"{filename}.json"
    output_path.write_text(json.dumps(prompt_data, indent=2))
```

## CLI Options and Flags

- `--fail-fast` / `--no-fail-fast` (default: `--fail-fast`)
  - When `--fail-fast`: Exit immediately on first error
  - When `--no-fail-fast`: Continue syncing remaining prompts even if some fail, report all failures at end

## Functional Requirements

### Core Functionality

1. Validate required settings (`langsmith_api_key`, `langsmith_project`) are present
2. Initialize LangSmith client with API key from settings
3. Fetch all prompts from the configured LangSmith project
4. Create `/prompts` directory if it doesn't exist
5. For each prompt:
   - Sanitize prompt name for use as filename
   - Extract prompt content and model information
   - Save as `{sanitized_name}.json` in `/prompts` directory
   - Overwrite if file already exists

### Console Output

- Use rich library for colorized output (no emojis)
- Display clear progress messages:
  - Connection status
  - Number of prompts found
  - Progress while syncing each prompt
  - Success summary or error details
- Example output structure:
  ```
  Connecting to LangSmith...
  Connected to project: pr-indelible-hobby-77
  Fetching prompts...
  Found 8 prompts
  Syncing prompts to /prompts...
    Saved resume_template_prompt.json
    Saved gap_analysis_prompt.json
    ...
  Successfully synced 8 prompts
  ```

### Error Handling

- **Missing settings**: Exit with clear error message if `langsmith_api_key` or `langsmith_project` not configured
- **Connection errors**: Handle network failures and API errors gracefully
- **Per-prompt errors**:
  - With `--fail-fast` (default): Exit immediately on first error
  - With `--no-fail-fast`: Log error, continue with remaining prompts, report failures at end
- **File system errors**: Handle permission errors, disk full, etc.

## Implementation Notes

- Follow CLI best practices from `.cursor/rules/standards/cli/overview.mdc`
- Use lazy imports inside commands to keep CLI startup fast
- Use Python 3.12 type annotations throughout
- Include proper docstrings and type hints
- API documentation references:
  - [LangSmith Client.list_prompts](https://reference.langchain.com/python/langsmith/observability/sdk/client/#langsmith.client.Client.list_prompts)
  - [LangSmith Client.get_prompt](https://reference.langchain.com/python/langsmith/observability/sdk/client/#langsmith.client.Client.get_prompt)
  - [LangSmith Client.pull_prompt](https://reference.langchain.com/python/langsmith/observability/sdk/client/#langsmith.client.Client.pull_prompt)
  - [Managing Prompts Programmatically Guide](https://docs.smith.langchain.com/prompt_engineering/how_to_guides/manage_prompts_programatically)

## Dependencies

Add to `pyproject.toml`:

```toml
"langsmith>=0.1.0",
```

## Technical Details

- **Filename sanitization**: Replace characters invalid for filenames (e.g., `/`, `\`, `:`, `*`, `?`, `"`, `<`, `>`, `|`) with underscores or remove them
- **Path handling**: Use `pathlib.Path` for all file operations
- **Settings validation**: Use Pydantic Settings to load and validate environment variables
- **Existing config**: `src/config.py` already has `langsmith_api_key` and `langsmith_project` fields defined
