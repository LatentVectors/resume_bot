# Spec Tasks

## Tasks

- [x] 1. Update database models for single-resume-per-job
  - [x] 1.1 Edit `src/database.py`: remove `Job.resume_filename`
  - [x] 1.2 Extend `Resume` with `template_name: str`, `resume_json: str`, `pdf_filename: str | None`
  - [x] 1.3 Enforce uniqueness on `Resume.job_id` (SQLAlchemy `UniqueConstraint` or code-level guard)
  - [x] 1.4 Ensure `Resume.locked` usage aligns with `Job.applied_at`
  - [x] 1.5 Initialize/prepare DB reset path; confirm app boots without `resume_filename` references

- [x] 2. Implement Job service denorm and helpers
  - [x] 2.1 Add `get_resume_for_job(job_id: int) -> DbResume | None` to `app/services/job_service.py`
  - [x] 2.2 Update `refresh_denorm_flags(job_id)` to compute `has_resume` from `Resume` only
  - [x] 2.3 Ensure `set_status(..., status="Applied")` marks `Resume.locked = True`

- [x] 3. Create PDF rendering service
  - [x] 3.1 Add `app/services/render_pdf.py` module
  - [x] 3.2 Implement `render_resume_pdf(resume_data, template_name, dest_path)` using `src/features/resume/utils.render_template_to_pdf`
  - [x] 3.3 Implement `render_preview_pdf(resume_data, template_name, preview_path)`; ensure `data/resumes/previews/` exists
  - [x] 3.4 Centralize error logging with `logger.exception` on failures

- [x] 4. Implement Resume service APIs
  - [x] 4.1 Add `generate_resume_for_job(user_id, job_id, prompt, existing_draft)` in `app/services/resume_service.py`
  - [x] 4.2 Implement `save_resume(job_id, resume_data, template_name)` with UUID filename management and overwrite behavior
  - [x] 4.3 Implement `render_preview(resume_data, template_name)` returning preview `Path`
  - [x] 4.4 Remove/deprecate old resume generation flow that created a Job/filename

- [x] 5. Update agent node for summary/title
  - [x] 5.1 Edit `src/agents/main/nodes/generate_summary.py` to output both `professional_summary` and `title`
  - [x] 5.2 Adjust parsing/return types to structured output consumed by the graph

- [x] 6. Replace create node with assemble resume data
  - [x] 6.1 Remove `src/agents/main/nodes/create_resume.py`
  - [x] 6.2 Add `src/agents/main/nodes/assemble_resume_data.py` to assemble final `ResumeData`
  - [x] 6.3 Ensure no file I/O in the node

- [x] 7. Adjust agent graph and state to return `ResumeData`
  - [x] 7.1 Update `src/agents/main/state.py` to include `resume_data: ResumeData` in `OutputState`
  - [x] 7.2 Update `src/agents/main/graph.py` to end with assembled `ResumeData`
  - [x] 7.3 Verify node wiring for experience/skills/summary updates remains intact

- [x] 8. Update `src/generate_resume.py` wrapper
  - [x] 8.1 Change signature to return `ResumeData` (no filename)
  - [x] 8.2 Integrate with the updated graph and nodes
  - [x] 8.3 Smoke test to validate JSON structure matches `src/features/resume/types.ResumeData`

- [x] 9. Build Resume tab UI skeleton and state
  - [x] 9.1 Implement `app/pages/job_tabs/resume.py` with two-column layout and instructions textarea
  - [x] 9.2 Add Template dropdown using `list_available_templates`, default `resume_000.html`
  - [x] 9.3 Render editable fields: user identity (read/write), AI-editable (with robot icon indicator)
  - [x] 9.4 Implement dirty state tracking for field/template changes; enable Save when dirty
  - [x] 9.5 Disable Generate/Save/Preview if required identity fields missing; show warning

- [x] 10. Integrate Generate, Save, and Preview in UI
  - [x] 10.1 Wire Generate to `ResumeService.generate_resume_for_job` and apply returned draft
  - [x] 10.2 Wire Save to `ResumeService.save_resume`; clear dirty on success
  - [x] 10.3 Render preview after Generate (temporary) and after Save (persisted); embed PDF in right column
  - [x] 10.4 Disable Download while dirty; enable only when a persisted PDF exists
  - [x] 10.5 Enforce read-only when `job.applied_at` is set (hide Generate/Save, disable editing)

- [x] 11. Update Overview tab and navigation/session behavior
  - [x] 11.1 Edit `app/pages/job_tabs/overview.py` to fetch `Resume` and use `pdf_filename` for Download
  - [x] 11.2 Add `navigate_to_job(job_id)` in `app/pages/job_tabs/utils.py` to set session state and switch page
  - [x] 11.3 Edit `app/pages/job.py` to remove query param parsing; rely on `st.session_state['selected_job_id']` and `selected_job_tab`

- [x] 12. Simplify Home page and clean up old workflow
  - [x] 12.1 Replace content in `app/pages/home.py` with a simple welcome message
  - [x] 12.2 Remove/deprecate any homepage-driven resume generation code
  - [x] 12.3 Quick pass to remove remaining references to `Job.resume_filename`

- [ ] 13. Acceptance tests and denorm verification
  - [ ] 13.1 Service tests: agent generation modifies allowed fields; save overwrites same UUID
  - [ ] 13.2 Preview test: returns temp path and does not update DB or denorm
  - [ ] 13.3 Denorm test: `refresh_denorm_flags` true only when `pdf_filename` exists
  - [ ] 13.4 UI behavior smoke checks: dirty toggling, required field disabling, read-only after Applied


