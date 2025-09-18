## Sprint 005 — Job Detail: Resume Tab (Generation, Editing, Preview, Download)

### Overview
This sprint adds a complete resume workflow to the Job Detail page under the Resume tab. Users can:
- Generate a job-specific resume via the agent (with an instructions textbox)
- Edit resume fields inline (including identity fields per resume)
- Select a resume template
- Preview the resume as a PDF
- Save the resume (persist JSON + render PDF)
- Download the saved PDF

Key architectural decisions:
- Single resume per job (no versioning) enforced by a unique constraint on `resume.job_id`.
- Resume content is persisted as JSON according to the `src/features/resume/types.ResumeData` schema.
- PDF preview is rendered to a PDF file, not HTML, to guarantee WYSIWYG.
- Preview re-renders on Save and after agent updates; Download is enabled only when a persisted PDF exists.
- After a Job is marked Applied, the resume becomes immutable (backend-enforced) but is still downloadable.
- Query params are removed from Job detail routing; session state is the source of truth for `selected_job_id` and `selected_job_tab`.


### User Stories
1) Generate new resume for a job without an existing resume
   - As a user viewing a Job Detail page without a resume, I see a view with two columns. In the left column there is a textarea at the top with a button beneath it with the text "Generate". Below the textarea input there are input fields for all the resume content, where I can manually add in resume content. Some of the fields, like user name, have been pre-populated with info from my profile. The right column is blank with a message indicating there is no resume PDF yet.
   - I can enter high-level instructions and click Generate; the agent returns a draft resume tailored to the job. The resume fields are populated with this new data and a preview of the PDF is rendered in the right column.
   - I can edit the fields and choose a template.
   - I click Save to persist content and render the preview PDF.

2) Edit and refine an existing resume
   - As a user with an existing resume, I can modify editable fields, change the template, and give the agent new instructions to regenerate summary, bullets, title, or skills.
   - Unsaved changes are tracked (dirty state). Download is disabled while dirty; Save is enabled.
   - After Save, the preview PDF regenerates and Download is enabled.

3) View-only after application
   - Once a job is Applied, the Resume tab becomes read-only. Generate and Save controls disappear; Download remains available if a PDF exists.
   - If I have not saved a resume before setting the job to Applied, I can't create a resume and the tab shows me a message indicating this job has no resume associated with it.


### Data Model Changes
We will extend `src/database.py` and adjust related services.

New/updated schema (SQLModel):
- `Resume`
  - `id: int | None` (PK)
  - `job_id: int` (FK → Job.id, UNIQUE)
  - `template_name: str` (e.g., `resume_000.html`)
  - `resume_json: str` (serialized `ResumeData` JSON)
  - `pdf_filename: str | None` (UUID filename; may be empty if no PDF yet)
  - `locked: bool` (existing — set to True when job moves to Applied)
  - `created_at: datetime`
  - `updated_at: datetime`
  - Constraint: unique index on `job_id` to enforce one resume per job

Deletions/field removals:
- Remove `Job.resume_filename` (all usages must be replaced; see File Changes section).

Denormalized flags:
- `Job.has_resume` indicates whether a saved PDF exists.
  - Recomputed as: `has_resume = (Resume row exists for job_id) AND (pdf_filename is non-empty)`.

Resume JSON typing:
- When reading `resume_json` from DB, always parse into `src/features/resume/types.ResumeData` to maintain type safety in UI/service layers.

Uniqueness enforcement:
- Add (or simulate) a unique constraint on `Resume.job_id`. For SQLite with SQLModel, implement via SQLAlchemy `UniqueConstraint` in `__table_args__` or enforce in code (attempt get existing Resume row and update instead of insert).

Migration notes:
- This sprint may require resetting the local SQLite schema. This is fine. Do not worry about preserving data, just reset the database as needed.


### Agent Graph and Service Responsibilities
Agent scope:
- Input: full `ResumeData` object (current draft) plus `job_description`, `experience`, and optional `prompt`. (The experience be the same experience objects currently passed to the agent. These should not be confused with the resume experience. The experience objects passed to the agent currently include unstructured histories of the users work experience and can be used by the agent to produce resume bullet points.)
- Agent-modifiable fields only:
  - `ResumeData.title` (Candidate Title)
  - `ResumeData.professional_summary`
  - `ResumeData.experience[i].points`
  - `ResumeData.skills`
- Agent may re-order `experience` and `skills`.
- Output: a new `ResumeData` object (full), with modified fields applied.

Graph changes (under `src/agents/main/`):
- Replace `nodes/create_resume.py` with `nodes/assemble_resume_data.py` that assembles the final `ResumeData` payload (no PDF I/O in the graph).
- Update `nodes/generate_summary.py` to return both `professional_summary` and `title` via structured output.
- Keep `generate_experience.py` and `generate_skills.py` as-is.
- Update `state.py`:
  - Use current state representation with separate fields internally, but assemble and return these values as an assembled `ResumeData` object at the end.
  - `OutputState` should include `resume_data: ResumeData`.

Wrapper (`src/generate_resume.py`):
- Change `generate_resume(...) -> ResumeData` (return the assembled resume object), not a filename.

Service separation:
- Move all PDF rendering to `app/services/render_pdf.py`.
- The agent is responsible only for content generation/updates, not rendering or persistence.


### UI/UX — Resume Tab
File: `app/pages/job_tabs/resume.py`

Layout:
- Two columns `[3, 1]`.
  - Left column:
    - Instructions textarea (Filler text = “What should the AI change?”)
    - Buttons: Generate (agent), Save (persist + render PDF), Discard Changes
    - Template dropdown (default `resume_000.html`; sourced from `src/features/resume/utils.list_available_templates`)
    - Editable fields grouped by ownership:
      - User-only fields: `name`, `email`, `phone`, `linkedin_url`, `education` (pre-populated from profile on first load; editing here does not update the profile)
      - AI-editable fields (visually indicated with a materials icon that indicates AI/Robot): `title`, `professional_summary`, `experience.title`, `experience.points`, `skills`
  - Right column:
    - PDF preview (embedded). Re-renders:
      - On Save (always)
      - After agent update (using the returned draft)
    - Download button enabled only when a persisted PDF exists

State and behavior:
- Dirty state:
  - Any manual field change or template change marks the draft as dirty (unsaved).
  - While dirty: Save enabled, Download disabled.
  - On Save success: dirty cleared; Download enabled.
- Agent generate action:
  - Sends instructions + current draft to `ResumeService.generate_resume_for_job(...)`.
  - Applies returned draft to the form, marks dirty, and triggers preview render to a temporary preview path.
  - Download remains disabled until a Save persists the PDF.
- Missing required values:
  - If required identity fields for the template (e.g., name, email) are missing, disable Generate, Save, and Preview; surface a warning with a suggestion to update the profile or fill values inline on the resume form.
- Read-only when Applied:
  - If `job.applied_at is not None`, hide Generate and Save; disable editing of all fields; keep Download available if a PDF exists.
  - If no resume is saved for the job, the page should be empty except for a message indicating the job has no resume and resume generation is locked for this job.

Routing and session state:
- Use `st.session_state['selected_job_id']` and `st.session_state['selected_job_tab']` as the single source of truth.
- Remove query param reading from `app/pages/job.py`.
- Add a navigation util to set job and reset per-job state (see File Changes).


### Backend Services — Resume
File: `app/services/resume_service.py`

New/updated APIs:
- `generate_resume_for_job(user_id: int, job_id: int, prompt: str, existing_draft: ResumeData | None) -> ResumeData`
  - Validates job exists, job not Applied, and required identity fields if generation requires them.
  - Prepares input for the agent (merging profile and existing_draft into a `ResumeData`).
  - Reads and prepares Experience data for the user to pass to the agent.
  - Invokes agent to produce an updated `ResumeData` draft.
  - Returns draft (no persistence here).

- `save_resume(job_id: int, resume_data: ResumeData, template_name: str) -> Resume`
  - Enforces immutability if job Applied (rejects save).
  - Serializes `resume_data` to JSON; ensures `Resume` row exists (one per job). If none, create; if exists, update.
  - PDF rendering:
    - If a `Resume` row exists with a `pdf_filename`, overwrite the same file (keep the same UUID).
    - Else create a new UUID filename under `data/resumes/`.
  - Update `Job.has_resume` by recomputing denorm flags (see JobService section).
  - On PDF render failure: log via `logger.exception(e)`; persist JSON changes if safe; clear `pdf_filename` and surface UI error. The UI should offer a “Generate PDF” retry action.

- `render_preview(resume_data: ResumeData, template_name: str) -> Path`
  - Renders a temporary PDF (e.g., under `data/resumes/previews/{job_id}.pdf`) for display only. Does not update DB or the canonical `Resume.pdf`.

Deprecated/removed:
- Remove `ResumeService.generate_resume(...)` that created a new Job and filename.


### Job Service and Denorm Flags
File: `app/services/job_service.py`

Changes:
- Add helper to fetch the single resume for a job: `get_resume_for_job(job_id: int) -> DbResume | None`.
- Update `refresh_denorm_flags(job_id: int)`:
  - `has_resume = (Resume row exists for job_id)`.
  - Remove reliance on `Job.resume_filename` and remove `resume_filename` from the Job model.

Locking on Applied:
- `set_status(..., status="Applied")` should continue to set `applied_at` on first transition and mark `Resume.locked = True`.


### Files to Add / Edit / Delete

Add:
- Extend `app/pages/job_tabs/utils.py`.
  - `def navigate_to_job(job_id: int) -> None`:
    - If `job_id` changes, set `st.session_state['selected_job_id'] = job_id` and reset `selected_job_tab = 'Overview'` (using the tab enum) and any per-job session state (unsaved resume data, instructions).
    - Call `st.switch_page('app/pages/job.py')`.

Edit:
- `src/database.py`
  - Remove `Job.resume_filename` field.
  - Extend `Resume` model with `template_name` and `resume_json`; enforce uniqueness on `job_id`.

- `app/services/job_service.py`
  - Implement `get_resume_for_job(job_id)`.
  - Update `refresh_denorm_flags` to use `Resume` only; remove `Job.resume_filename` logic.

- `app/services/resume_service.py`
  - Implement `generate_resume_for_job`, `save_resume`, `render_preview` as defined above.
  - Remove/deprecate old generate flow that created a Job.

- `src/agents/main/nodes/generate_summary.py`
  - Update structured output to include `title` along with `professional_summary`.

- `src/agents/main/nodes/create_resume.py`
  - Replace with `assemble_resume_data.py` (assemble and return `ResumeData`; no file I/O).

- `src/agents/main/graph.py` and `src/generate_resume.py`
  - Adjust graph to end at assembled `ResumeData`.
  - Update wrapper to return `ResumeData`.

- `app/pages/job_tabs/resume.py`
  - Implement UI per the UX section: fields, template dropdown, instructions, Generate/Save/Discard controls, PDF preview, Download button, and Applied read-only logic.

- `app/pages/job_tabs/overview.py`
  - Replace download button logic to fetch `Resume` for the job and read its `pdf_filename` from `data/resumes/`.

- `app/pages/job.py`
  - Remove query param parsing; use `st.session_state['selected_job_id']` and `selected_job_tab`.
  - Keep segmented control; ensure tab state persists across reruns.

- `app/pages/home.py`
  - Replace old resume workflow content with a simple welcome message.

Delete/Deprecate:
- Any homepage-driven resume generation workflow code that duplicates the new Resume tab flow.


### Template Management
- Use existing utilities in `src/features/resume/utils.py`:
  - `list_available_templates(templates_dir)` to populate template dropdown.
  - `render_template_to_pdf(...)` for Save-time PDF rendering.
- Default template: `resume_000.html`.
- Changing the template marks the draft dirty and requires Save to re-render the persisted PDF.


### Preview and Download Behavior
- Preview
  - Re-renders on Save and immediately after agent updates using a temporary preview PDF file.
  - If required identity fields for rendering are missing, preview is disabled until filled.
  - “Always do full regeneration of the preview.”
- Download
  - Enabled only when a persisted `Resume.pdf` exists (i.e., after Save creates/overwrites `pdf_filename`).


### Immutability and Permissions
- Backend enforcement: if `job.applied_at` is not None, reject Generate/Save attempts in services.
- UI: hide/disable controls accordingly (Generate, Save, editing widgets).


### Error Handling
- PDF render failure on Save:
  - Log `logger.exception(e)`.
  - Attempt to keep `resume_json` persisted while leaving `pdf_filename` empty.
  - UI should show an error and offer “Generate PDF” to retry rendering and then update the row.


### Acceptance Criteria
- Resume Data
  - Resume JSON persists round-trip as `ResumeData` with full type validation.
  - Unique `Resume` per `job_id` enforced.
- UI Behavior
  - Empty state for jobs without a resume offering Generate.
  - Editing fields and template marks draft dirty; Download disabled, Save enabled.
  - Save writes JSON and PDF, updates preview, enables Download.
  - Agent Generate updates draft and preview, does not enable Download until Save.
  - After Applied, editing/Generate/Save disabled; Download remains if PDF exists.
- Routing
  - Navigation uses session state (no query params). Switching jobs resets per-job state.
- Denorm Flags
  - `Job.has_resume` reflects existence of a non-empty `pdf_filename` in `Resume`.
- Removal
  - No references remain to `Job.resume_filename`.


### Testing Checklist
- Services
  - Generate draft via agent; assert changes in `title`, `professional_summary`, `experience.title/points`, `skills`.
  - Save persists JSON, renders PDF, overwrites prior PDF with same UUID.
  - Render preview returns a temporary PDF path and does not alter DB.
  - Attempt Save when job Applied: expect rejection.
- UI
  - Dirty state toggling for manual edits and template changes.
  - Required identity fields missing: Generate/Save/Preview disabled; warning displayed.
  - After Save, preview updates and Download enabled.
- Denorm
  - `refresh_denorm_flags` sets `has_resume` True only when PDF exists.


### Implementation Notes
- Keep all core logic in `src/` and thin wrappers in `app/services/`.
- Use `src/features/resume/types.ResumeData` for typing and ensure all transforms return/accept this model.
- PDF files live under `data/resumes/`. For previews, use `data/resumes/previews/{job_id}.pdf` or similar; clean up previews opportunistically.
- Maintain coding standards and logging guidelines noted in project rules.


### Out of Scope (Future Work)
- LangGraph SQLite checkpointer and transcript UI (documented as future work; not included this sprint).
- User-level default template preference.
- Multi-version history per job.


