# Sprint Overview

## Goal

Consolidate the intake workflow from 3 steps to 2 steps by merging experience enhancement (step 2) and resume generation/refinement (step 3) into a single continuous conversation-based workflow.

## User Stories

### Primary User Story

As a job applicant, I want a single continuous conversation that helps me develop both my experience narrative and resume, so I can efficiently create tailored application materials without navigating between separate workflow stages.

### Supporting Stories

- As a user, I want to see gap and stakeholder analyses while crafting my resume, so I can ensure I'm addressing the key requirements and understand how hiring managers may perceive my background.
- As a user, I want to manually edit my resume at any time during the conversation, so I have full control over the final content and can make quick adjustments without relying solely on AI suggestions.
- As a user, I want the AI to generate resume drafts when appropriate during our conversation, so I can see concrete proposals without explicitly requesting them.
- As a user, I want to relaunch the intake conversation after completion, so I can continue refining my materials based on new insights or feedback.

## Key Changes

### 1. Workflow Consolidation

- **Combine steps 2 and 3** into a single "Step 2: Experience & Resume Development"
- **Eliminate step 3** entirely - all resume work happens in the new combined step 2
- Create a **continuous conversation** (no separation between experience and resume phases)
- The LLM will have access to `propose_resume_draft` tool and will determine when to call it during the conversation

### 2. Analysis Generation & Storage

- **Generate both gap_analysis AND stakeholder_analysis** when user submits step 1 (before step 2 renders)
- Add `stakeholder_analysis: str | None` field to `JobIntakeSession` database table (similar to existing `gap_analysis`)
- Both analyses stored as formatted markdown strings in the database (not JSON - naming reflects markdown content)
- Step 2 should not render until both analyses are ready

### 3. Updated Layout with Analysis Tabs

Use the existing `step3_resume.py` two-column layout as the foundation (already 90% of what we need):

**Left Column**: Continuous conversation chat interface (not a tab, persistent in left column)

**Right Column - 4 Tabs**:

1. **Gap Analysis** - Read-only markdown display from database
2. **Stakeholder Analysis** - Read-only markdown display from database
3. **Resume Content** - Editable form (existing from step3)
4. **Resume PDF** - PDF preview (existing from step3)

The analysis tabs serve as reference material for the user during the conversation and resume development. The existing step3_resume.py structure should be preserved and extended rather than rebuilt.

### 4. Unified Workflow Replaces Separate Experience and Resume Workflows

- The new combined workflow in `step2_experience_and_resume.py` will be self-contained
- **Delete** `experience_enhancement.py` entirely (no longer needed)
- **Delete** old `step2_experience.py` entirely (functionality absorbed into renamed step3)
- The renamed `step3_resume.py` will be extended to handle both experience conversation and resume generation in one continuous workflow

## Technical Implementation

### Database Changes

#### JobIntakeSession Model (`src/database.py`)

**Field Name Changes:**

```python
# Rename existing field for clarity (markdown content, not JSON)
gap_analysis_json → gap_analysis: str | None

# Add new field (markdown content, not JSON)
stakeholder_analysis: str | None = Field(default=None)
```

**Field to Remove:**

```python
conversation_summary: str | None  # No longer needed in combined workflow
```

**Complete Updated Schema:**

```python
class JobIntakeSession(SQLModel, table=True):
    """Tracks state of job intake workflow for resumption and analytics."""

    __table_args__ = (UniqueConstraint("job_id", name="uq_job_intake_session_job_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    current_step: int  # 1 or 2 (step 3 eliminated)
    step1_completed: bool = Field(default=False)
    step2_completed: bool = Field(default=False)
    step3_completed: bool = Field(default=False)  # Deprecated but kept for backwards compatibility
    gap_analysis: str | None = Field(default=None)  # Renamed from gap_analysis_json (stores markdown)
    stakeholder_analysis: str | None = Field(default=None)  # NEW (stores markdown)
    # conversation_summary removed - no longer needed
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### Service Layer Changes

#### JobService (`app/services/job_service.py`)

Create new method mirroring the existing `save_gap_analysis()` pattern:

- `save_stakeholder_analysis(session_id: int, stakeholder_analysis: str) -> DbJobIntakeSession | None`

Update existing method signature if needed:

- `save_gap_analysis(session_id: int, gap_analysis: str) -> DbJobIntakeSession | None` (parameter name change for clarity)

### Workflow Changes

#### Step 1 Completion (`step1_details.py`)

When user submits step 1:

1. Create/update job record
2. **Generate both analyses sequentially** (simplest approach for Streamlit compatibility):
   - `gap_analysis = analyze_job_experience_fit(...)` (existing)
   - `stakeholder_analysis = analyze_stakeholders(...)` (new)
3. Save each analysis immediately after generation:
   - `JobService.save_gap_analysis(session_id, gap_analysis)`
   - `JobService.save_stakeholder_analysis(session_id, stakeholder_analysis)`
4. Show spinner with progress indicator: "Analyzing job requirements and stakeholders..."
5. Once both complete, transition to step 2
6. **Error handling**: If either analysis fails or is missing when step 2 loads, block step 2 with error: "Unable to load analyses. Please restart intake flow."

#### New Stakeholder Analysis Workflow

Create `app/services/job_intake_service/workflows/stakeholder_analysis.py`:

- Function: `analyze_stakeholders(job_description: str, experiences: list[Experience]) -> str`
- Pattern: Mirror `gap_analysis.py` structure
- Prompt: Placeholder initially (production prompt added later)
- Returns: Formatted markdown string

#### Combined Experience & Resume Workflow

**File Rename Strategy**: Rename `step3_resume.py` → `step2_experience_and_resume.py` (since step3 already has 90% of what we need).

**Implementation Approach**: The renamed file will be the single unified workflow. Extend it to include experience conversation functionality, replacing the need for separate step2_experience.py and experience_enhancement.py files entirely.

**Message History:**

- Single continuous conversation (no separate step 2/step 3 histories)
- Persists when user navigates away and returns
- Remove step 3 message history code if still present

**Session State Structure:**

```python
st.session_state.step2_messages  # Single continuous chat history
st.session_state.step2_selected_version_id  # Currently selected resume version
st.session_state.step2_draft  # Current resume data (ResumeData object)
st.session_state.step2_dirty  # Boolean: has user manually edited content
st.session_state.step2_initialized  # Boolean: initialization flag
```

**Two-Column Layout (preserved from step3_resume.py):**

**Left Column**:

- Continuous conversation chat interface (not a tab, always visible)

**Right Column - 4 Tabs**:

1. **Gap Analysis** - Read-only markdown rendered with `st.markdown(session.gap_analysis)`
2. **Stakeholder Analysis** - Read-only markdown rendered with `st.markdown(session.stakeholder_analysis)`
3. **Resume Content** - Editable form showing empty template structure until draft created (uses existing step 3 implementation)
4. **Resume PDF** - PDF preview (uses existing step 3 implementation)

**Resume Display & Version Selection:**

- Use **existing step 3 implementation** for:
  - Resume form rendering
  - Version selector dropdown
  - PDF preview
  - Save/pin/version creation buttons
  - All existing behavior preserved exactly as-is
- If user switches to older version, system prompt references that version's content (see System Prompt Structure below)

**System Prompt Structure:**

- Single unified prompt for combined workflow
- Extend existing `run_resume_chat()` from `resume_refinement.py` to accept additional parameters
- Context variables:
  - `job_description` (existing)
  - `gap_analysis` (new - from database)
  - `stakeholder_analysis` (new - from database)
  - `current_resume_content` (existing - stringified content of currently selected version; reflects manual edits and version switches)
  - `work_experience` (new - user's experience records formatted for context)
- Tool available: `propose_resume_draft` (existing)
- Prompt: Placeholder initially (production prompt added later)
- **Note**: When user switches between versions, the `current_resume_content` variable updates to reflect the selected version, ensuring LLM and user view the same content

**Resume Draft Tool Behavior:**

The `propose_resume_draft` tool is the mechanism for the AI to create resume versions during the conversation.

**Tool Implementation (following LangChain tool calling patterns):**

The existing `propose_resume_draft` tool in `resume_refinement.py` already implements the correct pattern. It should be preserved and integrated into the new combined workflow.

**Tool Arguments (what LLM must provide):**

- `title` (str): Professional title/headline for the resume
- `professional_summary` (str): Professional summary tailored to the job
- `skills` (list[str]): List of skills relevant to the position
- `experiences` (list[ProposedExperience]): List of experience objects, each containing:
  - `experience_id` (int): Database ID of the experience record
  - `title` (str): Job title (can be refined from original)
  - `points` (list[str]): Bullet points describing achievements and responsibilities
- `education_ids` (list[int]): List of education record IDs to include
- `certification_ids` (list[int]): List of certification record IDs to include

**Tool Execution Flow:**

1. LLM calls tool with above arguments
2. System processes tool call with provided arguments
3. Tool fetches experience/education/certification details from database using IDs
4. Creates complete `ResumeData` object (including name, email, phone, linkedin from user record)
5. Saves draft as new resume version using `ResumeService.create_version()`
6. Returns tuple: (confirmation message string, version_id integer as artifact)
7. System creates `ToolMessage` with confirmation and appends to conversation
8. UI updates to display the newly created version

**Injected Arguments (automatically provided by system):**

- `job_id`, `user_id`, `template_name`, `parent_version_id`, `version_tracker` (using LangChain's `InjectedToolArg`)

**Additional Notes:**

- Manual edits by user are reflected in `current_resume_content` variable for subsequent AI turns
- The tool uses `@tool(response_format="content_and_artifact")` decorator (current LangChain pattern)
- The existing implementation in `resume_refinement.py` already follows this exact pattern

**Step Completion:**

- "Skip" button: Complete step 2 without pinning a version (existing behavior)
- "Next" button: Complete step 2 and pin selected version (existing behavior, no version requirement)

#### Workflow File Cleanup

The new unified workflow replaces both the experience and resume workflows:

- `step3_resume.py` → Renamed to `step2_experience_and_resume.py` and extended with experience conversation
- `step2_experience.py` → **Deleted entirely** (replaced by renamed step3)
- `experience_enhancement.py` → **Deleted entirely** (no longer needed, functionality absorbed into unified workflow)
- `resume_refinement.py` → Modified to extend `run_resume_chat()` with additional context parameters

### File Operations Summary

- **Create**:

  - `app/services/job_intake_service/workflows/stakeholder_analysis.py` (new analysis workflow)

- **Rename**:

  - `app/dialog/job_intake/step3_resume.py` → `app/dialog/job_intake/step2_experience_and_resume.py`

- **Modify**:

  - `resume_refinement.py` (extend `run_resume_chat()` with new context parameters: gap_analysis, stakeholder_analysis, work_experience; preserve existing `propose_resume_draft` tool)
  - `src/database.py` (rename `gap_analysis_json` → `gap_analysis`; add `stakeholder_analysis` field; remove `conversation_summary`)
  - `job_service.py` (add `save_stakeholder_analysis()` method; update `save_gap_analysis()` parameter names if needed)
  - `job_intake_flow.py` (route to new `step2_experience_and_resume.py`, skip step3 routing)
  - `step1_details.py` (add stakeholder analysis generation; update to use renamed `gap_analysis` field)
  - `step2_experience_and_resume.py` (the renamed step3 file - extend to include experience conversation at start)

- **Delete**:

  - `app/dialog/job_intake/step2_experience.py` (replaced by renamed step3)
  - `app/services/job_intake_service/workflows/experience_enhancement.py` (no longer needed)
  - Remove `conversation_summary` field and all related code from workflows (no longer needed)
  - Update all references from `gap_analysis_json` to `gap_analysis` throughout codebase

- **Do Not Touch**:
  - `app/pages/job_tabs/resume.py` and all job detail page components
  - User can relaunch intake conversation from job overview tab after completion

### Prompts

Placeholder prompts will be used initially for:

- Stakeholder analysis workflow
- Combined experience & resume conversation

Production prompts will be added in a follow-up update.

## Dependencies, Risks, and Assumptions

### Dependencies

1. **Both analyses must complete before step 2 renders**: The gap_analysis and stakeholder_analysis must both be successfully generated and saved to the database before the user can proceed to step 2. The conversation relies on these analyses being available.

2. **Existing step 3 UI components must be preserved**: The resume form rendering, version selector, PDF preview, and all related UI components from step3_resume.py must be migrated intact to maintain existing functionality.

3. **Resume service and version management**: The existing resume version creation, tracking, and selection logic must continue to work identically in the new combined step.

4. **Experience formatting utilities**: The workflow depends on existing experience formatting functions (`format_experience_with_achievements`) for providing context to the LLM.

### Risks

1. **UI Complexity**: Merging two distinct workflows (experience chat and resume editing) into a single interface with 5 tabs increases UI complexity. Risk of confusion if tabs don't provide clear context about their purpose.

   - **Mitigation**: Preserve existing step 3 UI patterns exactly; use clear tab labels; provide analysis tabs as read-only reference material.

2. **Conversation Context Length**: Adding gap_analysis, stakeholder_analysis, and work_experience to the system prompt significantly increases token usage. Risk of exceeding context limits in long conversations.

   - **Mitigation**: Use placeholder prompts initially to test context management; may need to implement context summarization or compression in production.

3. **Sequential Analysis Performance**: Generating two analyses sequentially before step 2 renders may feel slow to users, especially with longer job descriptions or experience histories.

   - **Mitigation**: Show clear progress indicator; acceptable tradeoff for Streamlit compatibility and simpler implementation.

4. **Backwards Compatibility**: Existing intake sessions in progress may have step 3 message history or conversation_summary data that could cause issues.

   - **Mitigation**: Clean handling of legacy data; graceful fallback if analyses missing; test with existing user data.

5. **Version Switching Context**: When user switches between resume versions mid-conversation, the LLM context must update correctly. Risk of confusion if context doesn't match displayed version.
   - **Mitigation**: Ensure `current_resume_content` variable always reflects selected version; test version switching behavior thoroughly.

### Assumptions

1. **Placeholder prompts are functional**: We assume placeholder prompts will be sufficient for initial development and testing, with production prompts added later without requiring architectural changes.

2. **Sequential generation acceptable**: We assume sequential analysis generation (vs parallel) provides acceptable performance for the user experience.

3. **No database migrations needed**: We assume SQLModel will handle schema changes automatically in development without explicit migrations.

4. **Existing conversation patterns work**: We assume the existing conversation patterns from step 2 (experience) and step 3 (resume) can be seamlessly merged without fundamental changes to how users interact with the AI.

5. **Production data safety**: **CRITICAL ASSUMPTION** - All implementation and testing must be done against the existing production database without creating or modifying any data. Use existing user data for verification only; no test data insertion or updates allowed.

## Implementation Constraints

### Database Safety - CRITICAL

**⚠️ DO NOT modify the database during implementation or testing.**

This is **not a test database**. The following operations are **STRICTLY PROHIBITED**:

- ❌ Creating new jobs, users, experiences, or any records
- ❌ Updating existing records
- ❌ Deleting any data
- ❌ Running database migrations that alter existing data
- ❌ Any INSERT, UPDATE, or DELETE operations

**Allowed operations:**

- ✅ Reading existing data (SELECT queries only)
- ✅ Inspecting schema structure
- ✅ Verifying field definitions and relationships
- ✅ Testing with existing user data in read-only mode

**For testing:**

- Use the existing user and existing jobs/experiences
- Verify UI rendering and data display only
- Do not complete any workflows that would save to database
- Do not trigger any LLM calls that would create new records
