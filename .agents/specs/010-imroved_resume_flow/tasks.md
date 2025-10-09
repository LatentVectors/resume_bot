# Spec Tasks

## Tasks

- [x] 1. Update Experience data model and create Achievement model
  - [x] 1.1 Add `company_overview: str | None`, `role_overview: str | None`, and `skills: list[str]` fields to Experience model in `src/database.py`
  - [x] 1.2 Create Achievement model with `id`, `experience_id` (FK), `content`, `order`, `created_at`, `updated_at` fields
  - [x] 1.3 Update database manager to handle JSON field for skills array in Experience
  - [x] 1.4 Add database migration logic to create Achievement table and add new Experience columns
  - [x] 1.5 Test backward compatibility: verify existing experiences work without new fields

- [x] 2. Create JobIntakeSession and JobIntakeChatMessage models
  - [x] 2.1 Create JobIntakeSession model with `job_id` (unique FK), `current_step`, step completion flags, `gap_analysis_json`, `conversation_summary`, timestamps
  - [x] 2.2 Create JobIntakeChatMessage model with `session_id` (FK), `step`, `messages` (JSON), `created_at`
  - [x] 2.3 Add unique constraint on JobIntakeSession.job_id
  - [x] 2.4 Register new models with database manager and verify table creation
  - [x] 2.5 Test session CRUD operations and message storage/retrieval

- [x] 3. Create ExperienceService for Experience and Achievement operations
  - [x] 3.1 Create `app/services/experience_service.py` with ExperienceService class
  - [x] 3.2 Implement `update_experience_fields(experience_id, company_overview?, role_overview?, skills?)` method
  - [x] 3.3 Implement `add_achievement(experience_id, content, order?)` method
  - [x] 3.4 Implement `update_achievement(achievement_id, content)` method
  - [x] 3.5 Implement `delete_achievement(achievement_id)` and `reorder_achievements(experience_id, achievement_ids_in_order)` methods
  - [x] 3.6 Implement `get_experience_with_achievements(experience_id)` method returning tuple of experience and achievements
  - [x] 3.7 Test all service methods with various inputs and edge cases

- [x] 4. Extend JobService with intake session management methods
  - [x] 4.1 Add `create_intake_session(job_id) -> JobIntakeSession` method to JobService
  - [x] 4.2 Add `get_intake_session(job_id) -> JobIntakeSession | None` method
  - [x] 4.3 Add `update_session_step(session_id, step, completed=False)` method
  - [x] 4.4 Add `save_gap_analysis(session_id, gap_analysis_json)` and `save_conversation_summary(session_id, summary)` methods
  - [x] 4.5 Add `complete_session(session_id)` method to set completed_at timestamp
  - [x] 4.6 Test session lifecycle: create → update steps → save analysis/summary → complete

- [x] 5. Create ChatMessageService for chat history persistence
  - [x] 5.1 Create `app/services/chat_message_service.py` with ChatMessageService class
  - [x] 5.2 Implement `append_messages(session_id, step, messages_json)` method
  - [x] 5.3 Implement `get_messages_for_step(session_id, step) -> list[dict]` method
  - [x] 5.4 Implement `get_full_conversation(session_id) -> dict[int, list[dict]]` method
  - [x] 5.5 Test message persistence with various LangChain message formats
  - [x] 5.6 Verify JSON serialization/deserialization works correctly

- [x] 6. Update profile page experience form with new fields
  - [x] 6.1 Update `app/dialog/experience_dialog.py` to add "Company Overview" text area field (optional)
  - [x] 6.2 Add "Role Overview" text area field (optional)
  - [x] 6.3 Add "Skills" multi-select or tag input field for array of strings
  - [x] 6.4 Update form submission to save new fields via ExperienceService
  - [x] 6.5 Ensure form displays both new and legacy experience records correctly
  - [x] 6.6 Test creating/editing experiences with new fields

- [x] 7. Add achievement management UI to profile page
  - [x] 7.1 Create `show_add_achievement_dialog(experience_id)` function in experience_dialog.py or new achievement_dialog.py
  - [x] 7.2 Create `show_edit_achievement_dialog(achievement_id)` function
  - [x] 7.3 Create `show_delete_achievement_dialog(achievement_id)` with confirmation
  - [x] 7.4 Update `app/pages/profile.py` to display "Achievements" section within each experience
  - [x] 7.5 Add achievement list display with edit/delete buttons and reorder capability
  - [x] 7.6 Implement reorder functionality (drag-drop or up/down buttons) calling `reorder_achievements()`
  - [x] 7.7 Test full achievement CRUD workflow

- [x] 8. Implement gap analysis feature module
  - [x] 8.1 Create `src/features/jobs/gap_analysis.py` file
  - [x] 8.2 Define GapAnalysisReport Pydantic model with `matched_requirements`, `partial_matches`, `gaps`, `suggested_questions` fields
  - [x] 8.3 Implement `analyze_job_experience_fit(job_description: str, experiences: list[Experience]) -> GapAnalysisReport` function
  - [x] 8.4 Create comprehensive LLM prompt for gap analysis (extract requirements, match to experience, identify gaps/partials)
  - [x] 8.5 Use structured LLM output with Pydantic model validation
  - [x] 8.6 Add error handling for LLM failures (return empty report with error flag)
  - [x] 8.7 Test with various job descriptions (technical, non-technical, entry-level, senior) and experience levels

- [x] 9. Implement intake context summarization and resume generation
  - [x] 9.1 Create `src/features/jobs/intake_context.py` file
  - [x] 9.2 Implement `summarize_intake_conversation(messages: list[dict], gap_analysis: GapAnalysisReport) -> str` function
  - [x] 9.3 Create prompt to extract key insights, context, motivations from chat history (2-4 paragraph summary)
  - [x] 9.4 Implement `generate_resume_from_conversation(job_id, user_id, conversation_summary, chat_history) -> ResumeData` function
  - [x] 9.5 Fetch user profile data and experiences (including achievements) from database
  - [x] 9.6 Integrate with existing resume generation agent, enriching with conversation context
  - [x] 9.7 Test summarization quality and resume generation with/without conversation context

- [x] 10. Create intake flow dialog with Step 1 (Job Details)
  - [x] 10.1 Create `app/dialog/job_intake_flow.py` with main `show_job_intake_dialog()` function using @st.dialog
  - [x] 10.2 Initialize session_state.current_step if not present
  - [x] 10.3 Implement step routing logic based on current_step (1, 2, or 3)
  - [x] 10.4 Implement `render_step1_details(initial_title, initial_company, initial_description)` function
  - [x] 10.5 Display "Step 1 of 3: Job Details" progress indicator (plain text)
  - [x] 10.6 Render form with title, company, description, favorite fields
  - [x] 10.7 Add "Next" button (enabled only when required fields filled)
  - [x] 10.8 On Next: save job via JobService, create intake session, set current_step=2, st.rerun()
  - [x] 10.9 Test Step 1 independently and verify job/session creation

- [x] 11. Implement Step 2 (Experience Gap Filling) in intake dialog
  - [x] 11.1 Implement `render_step2_experience(job_id)` function in job_intake_flow.py
  - [x] 11.2 Display "Step 2 of 3: Experience Review" progress indicator
  - [x] 11.3 Run gap analysis and display report as first AI message (plain text, non-editable)
  - [x] 11.4 Set up LangChain chat model with tool binding (propose_experience_update, propose_achievement_update, propose_new_achievement)
  - [x] 11.5 Implement chat interface with message history in session state
  - [x] 11.6 Render proposal cards when AI makes tool calls (editable form with Accept/Reject buttons)
  - [x] 11.7 On Accept: save via ExperienceService, update chat context; On Reject: send feedback to AI
  - [x] 11.8 Add "Skip" (always enabled) and "Next" (enabled after ≥1 user message) buttons
  - [x] 11.9 On Skip/Next: run conversation summarization, save summary, set current_step=3, st.rerun()
  - [x] 11.10 Test chat functionality, tool calling, proposal acceptance/rejection

- [x] 12. Implement Step 3 (Resume Refinement) in intake dialog
  - [x] 12.1 Implement `render_step3_resume(job_id)` function in job_intake_flow.py
  - [x] 12.2 Display "Step 3 of 3: Resume Review" progress indicator
  - [x] 12.3 Generate initial resume using `generate_resume_from_conversation()` and create first ResumeVersion
  - [x] 12.4 Create two-column layout: left=chat interface, right=resume preview/edit
  - [x] 12.5 Add version selector dropdown at top of right column
  - [x] 12.6 Add toggle between PDF preview and editable form, copy/download buttons
  - [x] 12.7 Set up LangChain chat model with single `update_resume_draft` tool accepting full ResumeData
  - [x] 12.8 On tool call: save new ResumeVersion, update preview, return confirmation to chat
  - [x] 12.9 Handle manual edits: save new ResumeVersion when user edits form
  - [x] 12.10 Update AI system instructions when user switches versions
  - [x] 12.11 Add "Skip" (always enabled) and "Next" (enabled when version selected) buttons
  - [x] 12.12 On Next: pin version via ResumeService.pin_canonical(), complete session, navigate to job detail
  - [x] 12.13 On Skip: complete session without pinning, navigate to job detail
  - [x] 12.14 Test resume chat, version management, pinning workflow

- [x] 13. Integrate intake flow with home page
  - [x] 13.1 Update `app/pages/home.py` "Save" button handler
  - [x] 13.2 Keep existing extraction logic using `extract_title_company()`
  - [x] 13.3 Change dialog call from `show_save_job_dialog()` to `show_job_intake_dialog()`
  - [x] 13.4 Pass extracted title/company and description to intake dialog
  - [x] 13.5 Add error handling with user-friendly messages
  - [x] 13.6 Test end-to-end flow from home page through all 3 steps

- [x] 14. Add resume intake flow button to job detail overview tab
  - [x] 14.1 Update `app/pages/job_tabs/overview.py` to add intake flow button
  - [x] 14.2 Check job status: hide button if status is "Applied"
  - [x] 14.3 Get JobIntakeSession for job to determine resume vs restart state
  - [x] 14.4 If session incomplete: set current_step from session.current_step
  - [x] 14.5 If session complete/missing: set current_step = 1
  - [x] 14.6 Add button with `edit_note` icon and "Resume job intake workflow" text/tooltip
  - [x] 14.7 On click: set session_state.current_step and open show_job_intake_dialog()
  - [x] 14.8 Test resume from each step (1, 2, 3) and restart scenarios

- [x] 15. End-to-end testing and validation
  - [x] 15.1 Test complete flow: home page → Step 1 → Step 2 → Step 3 → job detail
  - [x] 15.2 Test Skip button at Step 2 (verify summarization runs)
  - [x] 15.3 Test Skip button at Step 3 (verify no pinning, session completes)
  - [x] 15.4 Test interruption at each step and resumption using overview button
  - [x] 15.5 Test with various job descriptions and experience combinations
  - [x] 15.6 Verify backward compatibility: legacy experiences work throughout flow
  - [x] 15.7 Verify NO Response records created during flow
  - [x] 15.8 Test version history visible in job detail resume tab
  - [x] 15.9 Verify LLM failure graceful degradation at each step
  - [x] 15.10 Confirm all button enablement rules enforced correctly

