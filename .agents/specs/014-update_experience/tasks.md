# Spec Tasks

## ⚠️ CRITICAL: Database Safety Constraint

**DO NOT MODIFY THE DATABASE IN ANY WAY DURING DEVELOPMENT, TESTING, OR CODE CHECKS.**

The database contains mission-critical live data that must not be modified, added to, or deleted from under any circumstances. All development and testing must use read-only operations only. See the spec document for full details.

## Tasks

- [x] 1. Database Schema: Add Enums and ExperienceProposal Table

  - [x] 1.1 Add `ProposalType` enum with values: achievement_add, achievement_update, achievement_delete, skill_add, skill_delete, role_overview_update, company_overview_update
  - [x] 1.2 Add `ProposalStatus` enum with values: pending, accepted, rejected
  - [x] 1.3 Create `ExperienceProposal` SQLModel table with fields: id, session_id, proposal_type, experience_id, achievement_id (nullable), proposed_content, original_proposed_content, status, created_at, updated_at
  - [x] 1.4 Update `JobIntakeSession` model: modify current_step field comment to indicate valid values are 1, 2, or 3, remove deprecation note from step3_completed field
  - [x] 1.5 **DO NOT RUN MIGRATIONS**: Schema changes must be reviewed and applied separately. Only define the models - do not execute any database modifications

- [x] 2. DatabaseManager: Add ExperienceProposal CRUD Methods

  - [x] 2.1 Implement `add_experience_proposal(proposal: ExperienceProposal) -> int` method (read-only validation only - do not execute inserts)
  - [x] 2.2 Implement `get_experience_proposal(proposal_id: int) -> ExperienceProposal | None` method (read-only - safe to test)
  - [x] 2.3 Implement `list_session_proposals(session_id: int) -> list[ExperienceProposal]` method (read-only - safe to test)
  - [x] 2.4 Implement `update_experience_proposal(proposal_id: int, **updates) -> ExperienceProposal | None` method (read-only validation only - do not execute updates)
  - [x] 2.5 Implement `delete_experience_proposal(proposal_id: int) -> bool` method (read-only validation only - do not execute deletes)

- [x] 3. Diff Utility: Create HTML Diff Generation Function

  - [x] 3.1 Create `/Users/mjlindow/projects/resume/app/shared/diff_utils.py` file
  - [x] 3.2 Implement `generate_diff_html(original: str, proposed: str) -> str` function using `difflib.SequenceMatcher.get_opcodes()`
  - [x] 3.3 Generate HTML with `<span class="diff-added">` for additions (green) and `<span class="diff-deleted">` for deletions (red strikethrough)
  - [x] 3.4 Handle character-level operations from get_opcodes() to build complete HTML string
  - [x] 3.5 Add docstring explaining function behavior and return format

- [x] 4. Pydantic Model: Create Structured Output Schema

  - [x] 4.1 Review `/Users/mjlindow/projects/resume/prompts/extract_experience_updates.json` to understand schema structure
  - [x] 4.2 Create Pydantic models matching the schema: WorkExperienceEnhancementSuggestions with nested models for role_overviews, company_overviews, skills, and achievements
  - [x] 4.3 Ensure models support both ADD and UPDATE operations for achievements (oneOf pattern)
  - [x] 4.4 Place models in appropriate location (likely in workflow file or separate models file)

- [x] 5. Extraction Workflow: Implement Experience Extraction Logic

  - [x] 5.1 Create `/Users/mjlindow/projects/resume/app/services/job_intake_service/workflows/experience_extraction.py` file
  - [x] 5.2 Follow patterns from existing workflow files (gap_analysis.py, stakeholder_analysis.py, resume_refinement.py)
  - [x] 5.3 Create workflow function that takes Step 2 chat messages and all user experiences as input
  - [x] 5.4 Implement placeholder/mocked system prompt (to be replaced with LangSmith prompt later)
  - [x] 5.5 Configure structured output to return Pydantic model instance matching the schema
  - [x] 5.6 Return validated Pydantic model with type-safe structured output

- [x] 6. JobIntakeService: Add Proposal Management Methods

  - [x] 6.1 Implement `extract_experience_proposals(session_id: int, job_id: int) -> list[ExperienceProposal]`: call workflow, convert Pydantic output to ExperienceProposal records. **DO NOT PERSIST TO DATABASE** - return in-memory objects only for development
  - [x] 6.2 Implement `get_pending_proposals(session_id: int) -> list[ExperienceProposal]`: retrieve all pending proposals for a session (read-only - safe to test)
  - [x] 6.3 Implement `update_proposal_content(proposal_id: int, new_content: dict) -> ExperienceProposal`: update proposal with user edits (read-only validation only - do not execute updates)
  - [x] 6.4 Implement `revert_proposal_to_original(proposal_id: int) -> ExperienceProposal`: restore original AI-generated content (read-only validation only - do not execute updates)
  - [x] 6.5 Implement `accept_proposal(proposal_id: int) -> bool`: apply proposal to Experience/Achievement records (handle all proposal types: skills add/delete, achievement add/update/delete, overview updates). **DO NOT EXECUTE DATABASE MODIFICATIONS** - validate logic only
  - [x] 6.6 Implement `reject_proposal(proposal_id: int) -> bool`: mark proposal as rejected (read-only validation only - do not execute updates)

- [x] 7. Step 3 UI: Create Proposal Display and Interaction Components

  - [x] 7.1 Create `/Users/mjlindow/projects/resume/app/dialog/job_intake/step3_experience_proposals.py` file following step1/step2 patterns
  - [x] 7.2 Implement main render function that groups proposals by experience and displays sections in order: Company Overview, Role Overview, Skills, Achievements
  - [x] 7.3 Create proposal card component with proposal type badge (Material icons with colors: add=green, edit=blue, delete=red)
  - [x] 7.4 Implement view mode: display content with diffs for updates, direct display for additions, skill badges (green for new, red strikethrough for deletions)
  - [x] 7.5 Implement edit mode: separate inputs for achievement title/content, individual skill inputs with add/remove buttons, textarea for overviews
  - [x] 7.6 Add action buttons: Edit, Accept, Reject (view mode), Cancel, Save (edit mode), Revert to Original (when edited)
  - [x] 7.7 Handle rejected proposal state: grayed out/disabled appearance

- [x] 8. Step 3 UI: Implement Empty State and Completion Flow

  - [x] 8.1 Display "No experience updates detected from your conversation" message when no proposals exist
  - [x] 8.2 Add "Next" button that completes workflow and navigates to job page
  - [x] 8.3 Allow "Next" button even with pending proposals (they remain in database but are not applied)
  - [x] 8.4 Handle multiple proposals for same achievement: display as adjacent cards

- [x] 9. Job Intake Flow Integration: Add Step 3 Routing

  - [x] 9.1 Update `/Users/mjlindow/projects/resume/app/dialog/job_intake_flow.py` to import step3_experience_proposals module
  - [x] 9.2 Add conditional rendering for step 3 when `st.session_state.current_step == 3`
  - [x] 9.3 Modify Step 2 "Next" button handler: show spinner, call `extract_experience_proposals()`, increment current_step to 3, rerun
  - [x] 9.4 Handle extraction workflow errors: show error message and allow user to skip Step 3

- [x] 10. Error Handling and Edge Cases

  - [x] 10.1 Add error handling for extraction workflow failures with user-friendly messages
  - [x] 10.2 Add error handling for proposal application failures (show toast, keep proposal in pending state)
  - [x] 10.3 Add logging for all errors with appropriate context
  - [x] 10.4 Handle session state management: use `step3_editing_proposal_id` and `step3_edit_content` keys
  - [x] 10.5 Validate proposal data before applying (check experience/achievement IDs exist, validate content) - use read-only queries only
  - [x] 10.6 **VERIFY NO DATABASE MODIFICATIONS**: Review all code to ensure no INSERT, UPDATE, or DELETE operations are executed during development/testing

- [x] 11. Safe Database Migration: Add ExperienceProposal Table
  - [x] 11.1 Create a manual migration script (e.g., `scripts/migrate_add_experience_proposal_table.py` or add to `DatabaseManager.migrate_schema()`) that safely adds the new table
  - [x] 11.2 Script should check if `experienceproposal` table already exists before attempting to create it
  - [x] 11.3 Use SQLModel's `create_all()` with `checkfirst=True` or equivalent SQLite-safe approach to avoid errors if table exists
  - [x] 11.4 Verify the script does NOT modify any existing tables or data (only creates new table)
  - [x] 11.5 Add comprehensive logging to track migration progress and success
  - [x] 11.6 Include rollback/error handling to ensure database integrity if migration fails
  - [x] 11.7 Test the migration script on a backup/test database first to verify it works safely
  - [x] 11.8 Delete the manual migration script.
