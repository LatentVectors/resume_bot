# Build out experience extraction

The main workflow is still missing that experience extraction and it's not updating and improving like I would want it to. So that's probably the next step - to develop out the experience enhancement process so that I don't have to repeat myself so much.

## ⚠️ CRITICAL: Database Safety Constraint

**DO NOT MODIFY THE DATABASE IN ANY WAY DURING DEVELOPMENT, TESTING, OR CODE CHECKS.**

The database contains mission-critical live data that must not be modified, added to, or deleted from under any circumstances. This includes:

- **No test data insertion**: Do not create test records, proposals, or any other data
- **No test data modification**: Do not update existing records for testing purposes
- **No test data deletion**: Do not delete any records
- **No schema migrations during development**: Schema changes must be reviewed and applied separately
- **Read-only operations only**: All development and testing must use read-only database operations

All code, tests, and validation checks must be designed to work with the existing database state without making any changes. If database operations are required for functionality, they must be clearly documented and only executed in production by authorized personnel.

## Workflow Structure

Add a step 3 to the job_intake_flow.py (after the current Step 2: Resume Development) where it recommends updates to the candidate's experience. The flow will be:

- Step 1: Job Details Confirmation
- Step 2: Experience & Resume Development (existing)
- Step 3: Experience Updates (NEW)

When the user clicks "Next" on Step 2, the system will automatically run an extraction workflow that analyzes the Step 2 conversation against ALL of the user's experiences to identify potential updates. If no updates are detected, Step 3 will display "No experience updates detected from your conversation" with a "Next" button to complete the workflow and navigate to the job page.

## Extraction Workflow

The workflow will use structured outputs to extract suggested updates to the candidate's experience by analyzing the complete Step 2 conversation (both user and AI messages) against all of the user's current work experiences. If a user mentions a new project or achievement from an older role during the conversation, the system will propose adding a new achievement to that older experience entry.

The workflow will be implemented in `./app/services/job_intake_service/workflows/experience_extraction.py` following the patterns and conventions in the existing workflow files (gap_analysis.py, stakeholder_analysis.py, resume_refinement.py).

### Input Data

- Complete Step 2 chat message history (user and AI messages)
- All user work experiences with achievements, skills, and overviews
- Job description, gap analysis, and stakeholder analysis are NOT included

### Structured Output Schema

The workflow uses structured outputs matching the schema in `./prompts/extract_experience_updates.json`. Proposed updates can include:

- **New skills**: Add new skills to an experience
- **New achievements**: Add new achievements with title and content
- **Updates to achievements**: Update existing achievement title and/or content
- **Updates to company overview**: Update the company_overview field
- **Updates to role overview**: Update the role_overview field

The structured outputs reference the ID of existing achievements when proposing updates. When updating an achievement, the AI can update the title, content, or both. When creating a new achievement, both title and content are required.

### System Prompt

For now, use a placeholder/mocked system prompt in the workflow file. In a later development phase, the prompt will be synced from LangSmith and merged into the workflow.

## Database Schema

### Enums

Add to `/Users/mjlindow/projects/resume/src/database.py` alongside existing enums:

```python
class ProposalType(str, Enum):
    achievement_add = "achievement_add"
    achievement_update = "achievement_update"
    achievement_delete = "achievement_delete"
    skill_add = "skill_add"
    skill_delete = "skill_delete"
    role_overview_update = "role_overview_update"
    company_overview_update = "company_overview_update"

class ProposalStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
```

### ExperienceProposal Table

Create a new `ExperienceProposal` table to persist proposals:

```python
class ExperienceProposal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="jobintakesession.id")
    proposal_type: ProposalType
    experience_id: int = Field(foreign_key="experience.id")
    achievement_id: int | None = Field(default=None, foreign_key="achievement.id")  # Only for achievement updates/deletes
    proposed_content: str  # JSON containing the full proposal data (Pydantic model serialized to JSON)
    original_proposed_content: str  # JSON of the original AI-generated proposal (for revert functionality)
    status: ProposalStatus  # enum: 'pending', 'accepted', 'rejected'
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

The `proposed_content` field stores a Pydantic model serialized to JSON, matching the structured output schema from the extraction workflow. The `original_proposed_content` stores the initial AI-generated proposal to enable revert functionality. This allows users to revert their edits back to the original AI suggestion without tracking intermediate changes.

Proposals persist across reopening the job_intake_flow, allowing users to return and complete the workflow later.

## Service Layer

### JobIntakeService Methods

Extend `/Users/mjlindow/projects/resume/app/services/job_intake_service/service.py` (JobIntakeService) with the following methods:

- `extract_experience_proposals(session_id: int, job_id: int) -> list[ExperienceProposal]`:
  - Calls the extraction workflow which returns a Pydantic model with structured output
  - Creates ExperienceProposal database records from the workflow output
  - Returns list of created proposal records
- `get_pending_proposals(session_id: int) -> list[ExperienceProposal]`: Retrieve all pending proposals for a session
- `update_proposal_content(proposal_id: int, new_content: dict) -> ExperienceProposal`: Update proposal with user edits
- `revert_proposal_to_original(proposal_id: int) -> ExperienceProposal`: Revert edited proposal back to original AI content
- `accept_proposal(proposal_id: int) -> bool`: Apply proposal to actual Experience/Achievement records
- `reject_proposal(proposal_id: int) -> bool`: Mark proposal as rejected and gray it out

### Extraction Workflow Return Type

The extraction workflow (`experience_extraction.py`) should:

- Take Step 2 chat messages and all user experiences as input
- Return a Pydantic model instance matching the structured output schema (validated type-safe output)
- The service layer (`JobIntakeService.extract_experience_proposals()`) is responsible for:
  - Calling the workflow
  - Converting the Pydantic model output to ExperienceProposal database records
  - Persisting the proposals to the database

### DatabaseManager Methods

Add CRUD methods to `/Users/mjlindow/projects/resume/src/database.py` DatabaseManager class:

- `add_experience_proposal(proposal: ExperienceProposal) -> int`: Create new proposal record
- `get_experience_proposal(proposal_id: int) -> ExperienceProposal | None`: Get proposal by ID
- `list_session_proposals(session_id: int) -> list[ExperienceProposal]`: Get all proposals for a session
- `update_experience_proposal(proposal_id: int, **updates) -> ExperienceProposal | None`: Update proposal fields
- `delete_experience_proposal(proposal_id: int) -> bool`: Delete proposal record

## Diff Utility

Create `/Users/mjlindow/projects/resume/app/shared/diff_utils.py` with a function that uses Python's `difflib.SequenceMatcher.get_opcodes()` to generate HTML diffs:

```python
def generate_diff_html(original: str, proposed: str) -> str:
    """Generate HTML diff showing additions and deletions.

    Uses difflib.SequenceMatcher.get_opcodes() to compare strings.
    Returns HTML with CSS classes for styling.

    Args:
        original: The existing content
        proposed: The proposed new content

    Returns:
        HTML string with styled spans:
        - <span class="diff-added">new text</span> for additions (green)
        - <span class="diff-deleted">old text</span> for deletions (red strikethrough)
        - Normal text for unchanged content
    """
```

### Diff Level and Styling

- Use the level of granularity provided by `get_opcodes()` (character-level operations)
- Deleted text: `<span class="diff-deleted">` styled with red color and strikethrough
- Added text: `<span class="diff-added">` styled with green color
- Unchanged text: rendered as-is without spans

### CSS Classes

```css
.diff-added {
  color: green;
  background-color: rgba(0, 255, 0, 0.1);
}

.diff-deleted {
  color: red;
  text-decoration: line-through;
  background-color: rgba(255, 0, 0, 0.1);
}
```

The diff visualization only applies to updates of existing content (achievement updates, overview updates). New achievements and new skills don't use diffs since they have no prior content to compare against.

## Step 3 UI Implementation

Create `/Users/mjlindow/projects/resume/app/dialog/job_intake/step3_experience_proposals.py` following the pattern of step1 and step2 modules.

### Layout Structure

Display proposals grouped by experience. For each experience with proposals:

1. **Experience Header**: Non-expandable title showing company name and job title (e.g., "Software Engineer at Acme Corp")
2. **Content Sections**: Display proposal cards in this fixed order:
   - Company Overview (if proposals exist)
   - Role Overview (if proposals exist)
   - Skills (if proposals exist)
   - Achievements (if proposals exist)
3. **Divider**: Place a divider between different experience sections

**Important**: Only display sections that have actual proposals. Do not show placeholders for empty sections.

### Proposal Cards

Each proposal card displays:

#### Proposal Type Badge

Use Material icons with color coding:

- **Add operations** (achievement_add, skill_add): `:material/add:` icon + green color + name (e.g., "Add Achievement", "Add Skill")
- **Update operations** (achievement_update, role_overview_update, company_overview_update): `:material/edit:` icon + blue color + name (e.g., "Update Achievement", "Update Role Overview")
- **Delete operations** (achievement_delete, skill_delete): `:material/delete:` icon + red color + name (e.g., "Delete Achievement", "Delete Skill")

#### View Mode (Default)

- **Header row**: Proposal type badge + Action buttons (Edit, Accept, Reject)
- **Content area**:
  - **Achievement updates**: Show separate diffs for title and content fields (both displayed)
  - **Overview updates**: Show full diff HTML comparing original vs proposed content
  - **Achievement additions**: Show the new title and content directly (no diff)
  - **Achievement deletions**: Show the achievement title and content that will be deleted
  - **Skill additions**: Show skills as green badges/pills for each new skill (only show skills not already in the experience's skill list)
  - **Skill deletions**: Show skills as red badges/pills with strikethrough for each skill being removed (only show skills that exist in the experience's skill list)
- **Card state**:
  - Default: Normal appearance
  - Rejected: Grayed out/disabled appearance (but still visible)

#### Edit Mode

When user clicks "Edit" button, transform the card:

- **Header row**: Proposal type badge + Action buttons (Cancel, Save)
- **Content area**:
  - **Achievement updates**: Separate text inputs for title and content
  - **Achievement additions**: Separate text inputs for title and content
  - **Skill additions**: Individual text inputs with add/remove buttons:
    - Display existing proposed skills as editable text inputs
    - Each skill input has a delete button to remove it
    - "Add Skill" button to add new skill inputs
    - User can edit existing skill entries, delete them, or add new ones
  - **Overview updates**: Single textarea with the proposed content
- "Cancel" button: Discards current edit session and returns to view mode with current content
- "Save" button: Saves edited content to `proposed_content` field and returns to view mode

#### Revert Functionality

If a proposal has been edited (i.e., `proposed_content != original_proposed_content`), show an additional "Revert to Original" button/link that calls `revert_proposal_to_original()` to restore the AI-generated content.

### Proposal Type Constraints

**Skills**:

- Can only be added or removed, never edited
- Skills are a discrete set - no partial edits
- Show as green if new (not in current list)
- Show as red with strikethrough if being removed (exists in current list)

**Overviews** (Company Overview, Role Overview):

- Can only be updated/edited, never deleted entirely
- Can be set to empty string (effectively deleting content, but field remains)
- Always show full diff for updates

**Achievements**:

- Can be added (new achievement with title and content)
- Can be updated (modify existing achievement title and/or content)
- Can be deleted (remove achievement entirely)
- For updates: show separate diffs for title and content fields

### Multiple Proposals for Same Item

If the AI suggests multiple updates to the same achievement (e.g., two different proposed contents for achievement ID 157), display both proposals as separate cards positioned adjacently so the user can quickly scan and see multiple options for the same achievement.

## Integration with Job Intake Flow

Update `/Users/mjlindow/projects/resume/app/dialog/job_intake_flow.py`:

1. **Step routing**: Add logic to render step 3 when `st.session_state.current_step == 3`
2. **Step transition**: When user clicks "Next" on Step 2:
   - Show spinner/progress indicator
   - Call `JobIntakeService.extract_experience_proposals(session_id, job_id)`
   - Increment `current_step` to 3
   - Rerun to display Step 3
3. **Empty state**: If no proposals were generated, Step 3 displays the empty state message with "Next" button that completes the workflow
4. **Step 3 completion**: User can click "Next" on Step 3 even if some proposals are still pending (neither accepted nor rejected). Pending proposals remain in the database but are not applied. The workflow completes and navigates to the job page.

Update the `JobIntakeSession` model in `/Users/mjlindow/projects/resume/src/database.py`:

- Modify `current_step` field comment to indicate valid values are now 1, 2, or 3
- Remove deprecation note from `step3_completed` field (no longer deprecated)

## Files to Create/Modify

### New Files

1. `/Users/mjlindow/projects/resume/app/dialog/job_intake/step3_experience_proposals.py` - Step 3 UI
2. `/Users/mjlindow/projects/resume/app/services/job_intake_service/workflows/experience_extraction.py` - Extraction workflow
3. `/Users/mjlindow/projects/resume/app/shared/diff_utils.py` - Diff HTML generation utility

### Modified Files

1. `/Users/mjlindow/projects/resume/app/dialog/job_intake_flow.py` - Add Step 3 routing
2. `/Users/mjlindow/projects/resume/app/services/job_intake_service/service.py` - Add proposal management methods
3. `/Users/mjlindow/projects/resume/src/database.py` - Add ExperienceProposal table and enums, update JobIntakeSession comments

## Technical Notes

### Proposal Application Logic

When a proposal is accepted:

- **New skills**: Append to experience's `skills` list (avoid duplicates by checking if skill already exists)
- **Delete skills**: Remove skills from experience's `skills` list
- **New achievement**: Call `ExperienceService.add_achievement()` with title and content
- **Update achievement**: Call `ExperienceService.update_achievement()` with new title/content
- **Delete achievement**: Call `ExperienceService.delete_achievement()` with achievement_id
- **Update overview**: Call `ExperienceService.update_experience_fields()` with new company_overview or role_overview (can be empty string to effectively clear the field)

### Session State Management

Use Streamlit session state keys with `step3_` prefix for Step 3 state:

- `step3_editing_proposal_id`: Tracks which proposal is currently being edited (None if none)
- `step3_edit_content`: Temporary storage for content being edited

### Error Handling

- If extraction workflow fails, show error message and allow user to skip Step 3
- If proposal application fails, show error toast and keep proposal in pending state
- Log all errors using the logger with appropriate context

### Database Safety

**CRITICAL**: All development, testing, and code validation must use read-only database operations only. The database contains mission-critical live data and must never be modified during development. See the Database Safety Constraint section at the top of this document for full details.

### Database Migration

The new `ExperienceProposal` table will be added to the database via a **manual migration script** that must be run separately after code development is complete. The migration script will:

- Safely check if the table already exists before creating it
- Only create the new table without modifying any existing tables or data
- Include comprehensive error handling and logging
- Be tested on a backup database first to verify safety

The migration script should follow the pattern of the existing `DatabaseManager.migrate_schema()` method, using SQLite-safe operations that check for table existence before creation. This ensures zero risk to existing mission-critical data.
