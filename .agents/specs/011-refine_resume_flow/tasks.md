# Spec Tasks

## Tasks

- [x] 1. Update Database Schema for Analysis Fields

  - [x] 1.1 In `src/database.py`, rename field `gap_analysis_json` to `gap_analysis` in `JobIntakeSession` model
  - [x] 1.2 Add new field `stakeholder_analysis: str | None = Field(default=None)` to `JobIntakeSession` model
  - [x] 1.3 Remove `conversation_summary` field from `JobIntakeSession` model
  - [x] 1.4 Update model docstring to reflect markdown storage (not JSON) for analysis fields
  - [x] 1.5 Verify schema compiles without errors (read-only check, no database operations)

- [x] 2. Create Stakeholder Analysis Workflow

  - [x] 2.1 Create new file `app/services/job_intake_service/workflows/stakeholder_analysis.py`
  - [x] 2.2 Implement `analyze_stakeholders(job_description: str, experiences: list[Experience]) -> str` function
  - [x] 2.3 Mirror structure of `gap_analysis.py` (import patterns, chain setup, helper functions)
  - [x] 2.4 Add placeholder system prompt for stakeholder analysis
  - [x] 2.5 Add proper error handling and logging
  - [x] 2.6 Export function in `__init__.py` if needed

- [x] 3. Update Job Service for Stakeholder Analysis

  - [x] 3.1 In `job_service.py`, create `save_stakeholder_analysis(session_id: int, stakeholder_analysis: str) -> DbJobIntakeSession | None`
  - [x] 3.2 Mirror implementation pattern of existing `save_gap_analysis()` method
  - [x] 3.3 Update `save_gap_analysis()` parameter name from `gap_analysis_json` to `gap_analysis` for consistency
  - [x] 3.4 Add proper validation and error handling
  - [x] 3.5 Update method docstrings to reflect markdown content (not JSON)

- [x] 4. Update Step 1 to Generate Both Analyses

  - [x] 4.1 In `step1_details.py`, import new `analyze_stakeholders` function
  - [x] 4.2 After gap analysis generation, add stakeholder analysis generation: `stakeholder_analysis = analyze_stakeholders(job_description, experiences)`
  - [x] 4.3 Save stakeholder analysis: `JobService.save_stakeholder_analysis(session.id, stakeholder_analysis)`
  - [x] 4.4 Update spinner text to: "Analyzing job requirements and stakeholders..."
  - [x] 4.5 Update all references from `gap_analysis_json` to `gap_analysis` in this file
  - [x] 4.6 Add error handling to block step 2 if either analysis fails with message: "Unable to load analyses. Please restart intake flow."

- [x] 5. Extend Resume Refinement Workflow

  - [x] 5.1 In `resume_refinement.py`, update `run_resume_chat()` function signature to accept: `gap_analysis: str`, `stakeholder_analysis: str`, `work_experience: str`
  - [x] 5.2 Add these new parameters to the system prompt context variables
  - [x] 5.3 Update `SYSTEM_PROMPT_TEMPLATE` to include placeholders for new context variables (placeholder text for now)
  - [x] 5.4 Ensure `propose_resume_draft` tool and all existing functionality remains unchanged
  - [x] 5.5 Update function docstring to document new parameters

- [x] 6. Rename and Extend Step3 to Combined Step2

  - [x] 6.1 Rename file `app/dialog/job_intake/step3_resume.py` to `app/dialog/job_intake/step2_experience_and_resume.py`
  - [x] 6.2 Update function name from `render_step3_resume()` to `render_step2_experience_and_resume()`
  - [x] 6.3 Update progress indicator from "Step 3 of 3: Resume Review" to "Step 2 of 2: Experience & Resume Development"
  - [x] 6.4 Update all session state keys from `step3_*` to `step2_*` throughout the file
  - [x] 6.5 Update all button keys and identifiers to use `step2` prefix instead of `step3`

- [x] 7. Add Analysis Tabs to UI

  - [x] 7.1 In `step2_experience_and_resume.py`, retrieve `gap_analysis` and `stakeholder_analysis` from session (via `JobService.get_intake_session()`)
  - [x] 7.2 In right column tabs section, add "Gap Analysis" tab as first tab
  - [x] 7.3 In "Gap Analysis" tab, render markdown with `st.markdown(session.gap_analysis)` in read-only container
  - [x] 7.4 Add "Stakeholder Analysis" tab as second tab
  - [x] 7.5 In "Stakeholder Analysis" tab, render markdown with `st.markdown(session.stakeholder_analysis)` in read-only container
  - [x] 7.6 Ensure existing "Resume Content" and "Resume PDF" tabs remain as tabs 3 and 4
  - [x] 7.7 Add error handling if analyses are None/missing

- [x] 8. Update Resume Chat Integration

  - [x] 8.1 In `step2_experience_and_resume.py`, locate where `run_resume_chat()` is called
  - [x] 8.2 Format work experience for context using `format_experience_with_achievements()` function
  - [x] 8.3 Pass `gap_analysis`, `stakeholder_analysis`, and formatted `work_experience` to `run_resume_chat()`
  - [x] 8.4 Ensure proper error handling if analyses are missing
  - [x] 8.5 Verify chat message handling and tool execution remain unchanged

- [x] 9. Update Intake Flow Routing

  - [x] 9.1 In `job_intake_flow.py`, import renamed function `render_step2_experience_and_resume` from new file location
  - [x] 9.2 Update step 2 routing to call `render_step2_experience_and_resume(st.session_state.intake_job_id)`
  - [x] 9.3 Remove step 3 routing entirely (elif for step 3)
  - [x] 9.4 Update any step progression logic to only handle steps 1 and 2
  - [x] 9.5 Verify dialog width and other settings remain appropriate

- [x] 10. Delete Deprecated Files

  - [x] 10.1 Delete file `app/dialog/job_intake/step2_experience.py`
  - [x] 10.2 Delete file `app/services/job_intake_service/workflows/experience_enhancement.py`
  - [x] 10.3 Search codebase for any imports of deleted files and remove them
  - [x] 10.4 Search for references to `render_step2_experience` function and verify none remain
  - [x] 10.5 Search for references to `experience_enhancement` functions/tools and verify none remain

- [x] 11. Update All gap_analysis_json References

  - [x] 11.1 Search codebase for all occurrences of `gap_analysis_json`
  - [x] 11.2 Replace with `gap_analysis` in all files (database queries, service methods, UI code)
  - [x] 11.3 Update any docstrings or comments mentioning `gap_analysis_json`
  - [x] 11.4 Verify no references to `gap_analysis_json` remain in codebase

- [x] 12. Remove conversation_summary References

  - [x] 12.1 Search codebase for all references to `conversation_summary` field
  - [x] 12.2 Remove any code that saves or retrieves `conversation_summary`
  - [x] 12.3 Remove `save_conversation_summary()` method from `JobService` if it exists
  - [x] 12.4 Remove any workflow code that generates conversation summaries
  - [x] 12.5 Verify no references to `conversation_summary` remain

- [x] 13. Verification and Testing (Read-Only)
  - [x] 13.1 Start application and verify database schema loads without errors
  - [x] 13.2 Navigate to job intake flow and verify step 1 renders correctly
  - [x] 13.3 Verify analysis tabs are present in UI (using existing data if available)
  - [x] 13.4 Verify chat interface renders in left column
  - [x] 13.5 Verify resume content and PDF tabs render correctly
  - [x] 13.6 Check for any console errors or warnings
  - [x] 13.7 Verify no database write operations are triggered during testing
  - [x] 13.8 Document any issues found for resolution
