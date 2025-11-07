## Overview

The resume_alignment_workflow prompt in LangSmith now includes a MessagesPlaceholder variable (`message_history`). This sprint updates the prompt sync system to properly handle MessagesPlaceholder inputs and refactors the resume refinement workflow to use the synced prompt instead of hard-coded templates.

## Problem Statement

The current `input_types.py` generator treats all prompt input variables as `str` types. The `resume_alignment_workflow` prompt contains a `MessagesPlaceholder` for `message_history`, which should be typed as `Sequence[BaseMessage]` from LangChain, not as a string.

Additionally, `resume_refinement.py` uses a hard-coded `SYSTEM_PROMPT_TEMPLATE` instead of the synced LangSmith prompt, creating maintenance overhead and drift between LangSmith and the codebase.

## Implementation Details

### 1. MessagesPlaceholder Type Detection

**Type Annotation Strategy:**

- MessagesPlaceholder variables will be typed as `Sequence[BaseMessage]`
- Import `BaseMessage` from `langchain_core.messages`
- Import `Sequence` from `collections.abc`
- This matches LangChain's native message handling

**JSON Structure Analysis:**

The prompt JSON files contain a `committed_prompt` object (loaded by default via `load_prompt()`) with this structure:

```json
{
  "committed_prompt": {
    "kwargs": {
      "input_variables": ["gap_analysis", "job_description", "message_history", ...],
      "messages": [
        {
          "id": ["langchain", "prompts", "chat", "SystemMessagePromptTemplate"],
          ...
        },
        {
          "id": ["langchain", "prompts", "chat", "HumanMessagePromptTemplate"],
          ...
        },
        {
          "id": ["langchain", "prompts", "chat", "MessagesPlaceholder"],
          "kwargs": {
            "variable_name": "message_history"
          }
        }
      ]
    }
  }
}
```

When `load_prompt()` deserializes this JSON, it creates Python objects where the third message becomes a `MessagesPlaceholder` instance with a `variable_name` attribute.

**Detection Method:**

After loading the prompt template in `generate_prompt_input_types()`:

1. Check if the loaded prompt has a `messages` attribute (ChatPromptTemplate will have this)
2. Iterate through each message in `prompt.messages`
3. Check the message type using `type(msg).__name__ == "MessagesPlaceholder"`
4. If true, extract the variable name: `msg.variable_name`
5. Store all MessagesPlaceholder variable names in a set: `message_placeholder_vars`
6. When generating TypedDict fields, check if the variable is in this set:
   - If yes: generate `variable_name: Sequence[BaseMessage]`
   - If no: generate `variable_name: str`

**Example Implementation Logic:**

```python
# After loading prompt
message_placeholder_vars = set()
if hasattr(prompt, 'messages'):
    for msg in prompt.messages:
        if type(msg).__name__ == "MessagesPlaceholder":
            message_placeholder_vars.add(msg.variable_name)

# When generating TypedDict fields
for var in input_vars:
    if var in message_placeholder_vars:
        field_type = "Sequence[BaseMessage]"
    else:
        field_type = "str"
```

### 2. Conditional Import Generation

The generated `input_types.py` file will only import message types if at least one prompt uses MessagesPlaceholder:

- Check if any prompts have MessagesPlaceholder during generation
- If yes, add: `from collections.abc import Sequence` and `from langchain_core.messages import BaseMessage`
- If no, keep the minimal imports (only `TypedDict`)

### 3. Update resume_refinement.py Workflow

**Current State Analysis:**

The synced `resume_alignment_workflow.json` has these input variables (lines 42-47, 188-193):

- `gap_analysis`
- `job_description`
- `message_history` (MessagesPlaceholder)
- `stakeholder_analysis`
- `work_experience`

The current `resume_refinement.py` workflow code also uses `current_resume`, which is **NOT** in the LangSmith prompt.

**Implementation Decision:**

Use only the variables defined in the synced LangSmith prompt. Remove `current_resume` from the workflow entirely to match the prompt's expected inputs. This aligns the code with the source of truth (LangSmith).

**Code Changes:**

1. Remove `SYSTEM_PROMPT_TEMPLATE` constant (lines 125-163)
2. Remove `_base_prompt = get_prompt(...)` line (line 120)
3. Remove manual `ChatPromptTemplate.from_messages()` construction (lines 329-336)
4. Load prompt: `_prompt = get_prompt(PromptName.RESUME_ALIGNMENT_WORKFLOW)`
5. Update chain construction: `_chain = _prompt | _llm_with_tools`
6. In `run_resume_chat()` function (starting line 34):
   - Remove `resume_data = ResumeData.model_validate_json(...)` (line 56)
   - Remove `current_resume_text = str(resume_data)` (line 57)
   - Remove `"current_resume": current_resume_text` from invoke call (line 98)
   - Keep only the variables that exist in the synced prompt: `message_history`, `job_description`, `gap_analysis`, `stakeholder_analysis`, `work_experience`
7. Remove TODO comment about updating LangSmith prompt (lines 165-166)

## Files Modified

**Files to Edit:**

1. **`src/core/prompts/input_types_generator.py`**

   - Add MessagesPlaceholder detection logic in `generate_prompt_input_types()`
   - Update `_generate_input_types_file()` to handle conditional imports
   - Modify field generation to use `Sequence[BaseMessage]` for message placeholders

2. **`src/core/prompts/input_types.py`** (auto-generated)

   - Will be regenerated with correct types via `python cli.py prompts sync`
   - Should include conditional imports when MessagesPlaceholder is detected

3. **`app/services/job_intake_service/workflows/resume_refinement.py`**
   - Remove hard-coded `SYSTEM_PROMPT_TEMPLATE` (lines 125-163)
   - Remove `_base_prompt` variable (line 120)
   - Remove manual chain construction (lines 329-336)
   - Update to use synced prompt directly
   - Remove TODO comment (lines 165-166)

**Files Referenced (No Changes):**

- `prompts/resume_alignment_workflow.json` - Read to understand structure
- `src/core/prompts/loader.py` - Already handles MessagesPlaceholder deserialization
- `src/core/prompts/names.py` - Already has RESUME_ALIGNMENT_WORKFLOW enum

## Implementation Order

1. **Update input_types_generator.py**

   - Add MessagesPlaceholder detection logic
   - Update type generation to handle message sequences
   - Add conditional import logic

2. **Run prompt sync command**

   - Execute: `python cli.py prompts sync`
   - Verify generated `input_types.py` has correct types
   - Verify `ResumeAlignmentWorkflowInput.message_history` is `Sequence[BaseMessage]`

3. **Update resume_refinement.py**

   - Remove hard-coded prompt template code
   - Remove `current_resume` variable and related code
   - Use `get_prompt()` to load synced prompt
   - Update chain construction to use loaded prompt
   - Update invoke call to only pass variables defined in the synced prompt
   - Verify all imports are correct

## Expected Outcomes

After this sprint:

1. **Type Safety:**

   - `input_types.py` correctly types `message_history` as `Sequence[BaseMessage]`
   - Type checkers will catch incorrect usage of message placeholder variables

2. **Code Simplification:**

   - `resume_refinement.py` uses synced prompt instead of hard-coded template
   - Single source of truth for prompt content (LangSmith)
   - Reduced code duplication and maintenance overhead

3. **Functional Behavior:**

   - Resume refinement workflow continues to work identically
   - Messages are properly passed through the chat interface
   - No user-facing changes in behavior

4. **Future Extensibility:**
   - Pattern established for handling MessagesPlaceholder in other prompts
   - Easy to update prompt content in LangSmith without code changes

## Scope Constraints

- **Focus:** Only update the resume_refinement workflow
- **Out of Scope:**
  - The `extract_experience_updates` prompt (defer to future sprint)
  - Test creation or updates
  - Other workflows using prompts
  - Manual verification testing (to avoid database state modifications)

## Technical Decisions

- Use LangChain's native `BaseMessage` type (not generic dicts)
- Tools and structured outputs remain defined in code (not in LangSmith)
- Prompt templates will be synced from LangSmith
- Use only the input variables defined in the synced prompt (remove `current_resume` from workflow)
