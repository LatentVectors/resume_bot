# Sprint Overview

This sprint refactors the prompt loading system to provide better type safety through separate generated files and simplifies the workflow integration.

## Goals

### 1. Simplify `get_prompt` Function

- `get_prompt()` should use overloads to return the appropriate prompt template type
- Return ONLY the prompt template (not a tuple with TypedDict)
- TypedDict classes are imported directly where needed, not returned from `get_prompt()`

### 2. Three Separate Generated Files

- `src/core/prompts/names.py` - PromptName enum (already exists)
- `src/core/prompts/input_types.py` - TypedDict classes for prompt inputs
- `src/core/prompts/get_prompt.py` - Type-safe get_prompt() function with overloads

Each file has a dedicated generator:

- `enum_generator.py` generates `names.py`
- `input_types_generator.py` generates `input_types.py` (ONLY TypedDict classes, no get_prompt function)
- `get_prompt_generator.py` generates `get_prompt.py` (NEW)

### 3. Public API Changes

- Export `get_prompt` and `PromptName` from `src/core/prompts/__init__.py`
- Remove `load_prompt` from public API (becomes internal implementation detail)
- `get_prompt()` is the main way to load prompts

### 4. Refactor Workflow Files

Refactor these workflow files to use the new pattern:

- `app/services/job_intake_service/workflows/gap_analysis.py`
- `app/services/job_intake_service/workflows/stakeholder_analysis.py`

Pattern:

```python
from src.core.prompts import PromptName, get_prompt
from src.core.prompts.input_types import GapAnalysisInput

_prompt = get_prompt(PromptName.GAP_ANALYSIS)
_chain = _prompt | _llm | StrOutputParser()

def analyze_job_experience_fit(job_description: str, experiences: list[Experience]) -> str:
    inputs: GapAnalysisInput = {
        "job_description": job_description,
        "work_experience": experience_summary,
    }
    return _chain.invoke(inputs)
```

**Note:** `resume_refinement.py` will be handled in a separate phase and is excluded from this sprint.

## Implementation Details

### Files to Create

1. **`src/core/prompts/get_prompt_generator.py`**

   - Generates `src/core/prompts/get_prompt.py`
   - Scans prompts directory and loads each prompt to detect runtime type
   - Creates overloaded `get_prompt()` function where each overload returns the specific concrete type
   - Implementation delegates to `load_prompt(name)`

   Example generated file:

   ```python
   # AUTO-GENERATED FILE - DO NOT EDIT MANUALLY
   from typing import Literal, overload
   from langchain_core.prompts.chat import ChatPromptTemplate
   from .loader import load_prompt
   from .names import PromptName

   @overload
   def get_prompt(name: Literal[PromptName.GAP_ANALYSIS]) -> ChatPromptTemplate: ...

   @overload
   def get_prompt(name: Literal[PromptName.STAKEHOLDER_ANALYSIS]) -> ChatPromptTemplate: ...

   def get_prompt(name: PromptName) -> ChatPromptTemplate:
       """Load a prompt template by name."""
       return load_prompt(name)
   ```

### Files to Modify

1. **`src/core/prompts/input_types_generator.py`**

   - Remove `get_prompt()` function generation
   - Generate ONLY TypedDict classes
   - Simplify output file structure

2. **`src/core/prompts/__init__.py`**

   - Change imports: `from .get_prompt import get_prompt`
   - Remove `load_prompt` from exports
   - Final exports: `["get_prompt", "PromptName"]`

3. **`src/core/prompts/cli.py`**

   - Import `generate_get_prompt` from `get_prompt_generator`
   - Call generators in sequence:
     1. `generate_prompt_enum()` → generates `names.py`
     2. `generate_prompt_input_types()` → generates `input_types.py`
     3. `generate_get_prompt()` → generates `get_prompt.py`

4. **`app/services/job_intake_service/workflows/gap_analysis.py`**

   - Update imports: `from src.core.prompts import PromptName, get_prompt`
   - Add: `from src.core.prompts.input_types import GapAnalysisInput`
   - Change: `_prompt = get_prompt(PromptName.GAP_ANALYSIS)` (remove tuple unpacking)
   - Add type annotation: `inputs: GapAnalysisInput = {...}`

5. **`app/services/job_intake_service/workflows/stakeholder_analysis.py`**
   - Update imports: `from src.core.prompts import PromptName, get_prompt`
   - Add: `from src.core.prompts.input_types import StakeholderAnalysisInput`
   - Change: `_prompt = get_prompt(PromptName.STAKEHOLDER_ANALYSIS)` (remove tuple unpacking)
   - Add type annotation: `inputs: StakeholderAnalysisInput = {...}`

## Success Criteria

1. Running `python cli.py prompts sync` generates all three files: `names.py`, `input_types.py`, `get_prompt.py`
2. `gap_analysis.py` and `stakeholder_analysis.py` successfully load prompts using `get_prompt()`
3. Type annotations using imported TypedDict classes provide IDE autocomplete and type checking
4. Application runs without import or runtime errors
5. `mypy` or `pyright` shows no type errors in refactored workflow files
