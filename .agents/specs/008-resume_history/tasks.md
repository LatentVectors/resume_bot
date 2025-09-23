# Spec Tasks

## Tasks

- [x] 1. Add ResumeVersion data model and enum (src/database.py)
  - [x] 1.1 Define `ResumeVersionEvent(StrEnum)` with values: `'generate' | 'save' | 'reset'`.
  - [x] 1.2 Create `ResumeVersion` SQLModel with fields: `id`, `job_id(FK)`, `version_index`, `parent_version_id`, `event_type`, `template_name`, `resume_json`, `created_by_user_id`, `created_at`.
  - [x] 1.3 Add uniqueness constraint on `(job_id, version_index)` and index `(job_id, created_at desc)`.
  - [x] 1.4 Leave `Resume` model intact; add deprecation comment on `pdf_filename` (deprecated per specs/008-resume_history, not used in runtime).
  - [x] 1.5 Ensure tables auto-create via existing `DatabaseManager._init_database()` without dropping others.

- [x] 2. Implement bytes-based PDF rendering utilities
  - [x] 2.1 In `src/features/resume/utils.py`, add `render_template_to_pdf_bytes(template_name: str, context: dict, templates_dir: Path) -> bytes`.
  - [x] 2.2 In `app/services/render_pdf.py`, add `render_resume_pdf_bytes(...)` and `render_preview_pdf_bytes(...)` that return bytes (no disk I/O) and delegate to utils.
  - [x] 2.3 Keep existing path-based helpers for any legacy usage, but prefer bytes in new code.

- [x] 3. Extend ResumeService for versions and bytes previews (app/services/resume_service.py)
  - [x] 3.1 Add `create_version(job_id, resume_data, template_name, event_type: ResumeVersionEvent, parent_version_id: int | None = None) -> DbResumeVersion`.
  - [x] 3.2 Add `list_versions(job_id: int) -> list[DbResumeVersion]` and `get_version(version_id: int) -> DbResumeVersion | None`.
  - [x] 3.3 Add `pin_canonical(job_id: int, version_id: int) -> DbResume` that writes canonical JSON/template to `Resume`.
  - [x] 3.4 Add `get_canonical(job_id: int) -> DbResume | None`.
  - [x] 3.5 Update `generate_resume_for_job(...)` to call `create_version(..., 'generate')` after producing the draft; do not touch canonical.
  - [x] 3.6 Update `save_resume(...)` to create a version with `event_type='save'`; do not update canonical.
  - [x] 3.7 Change `render_preview(...)` to return PDF bytes (not a file path) using the new bytes renderer.

- [x] 4. Update JobService denorm flags (app/services/job_service.py)
  - [x] 4.1 In `refresh_denorm_flags`, compute `has_resume` as True iff a `Resume` row exists for the job.
  - [x] 4.2 Remove reliance on `pdf_filename` anywhere in `JobService` (incl. `create_resume` paths if referenced).
  - [x] 4.3 Adjust logging/docstrings to reflect canonical-based `has_resume`.

- [x] 5. Update Resume tab UI for versioning and pinning (app/pages/job_tabs/resume.py)
  - [x] 5.1 Add right-aligned header controls: `< | dropdown | >` listing `v1..vN`; manage selected version in `st.session_state`.
  - [x] 5.2 Add Material pin icon to the right; filled when selected version is canonical, outlined otherwise; one-click pin with toast.
  - [x] 5.3 Load the selected version JSON into the editor; allow editing even for older versions; Generate/Save create a new head.
  - [x] 5.4 Replace preview to render from bytes and display via `pdf_viewer(pdf_bytes, ...)` (no file usage or paths).
  - [x] 5.5 Enforce download rules: enable only when selected is canonical AND editor is clean; otherwise disable with helpful tooltip.
  - [x] 5.6 Applied state: hide navigation, Generate/Save, and Pin; show only canonical preview and download (if clean).
  - [x] 5.7 Remove all `pdf_filename` references and persisted preview-path logic; clean up session keys accordingly.

- [x] 6. Update overview page download behavior (app/pages/job_tabs/overview.py)
  - [x] 6.1 Remove `pdf_filename` references and disk reads.
  - [x] 6.2 Show download only if `has_resume` is True and state is clean; fetch canonical bytes via `ResumeService`.
  - [x] 6.3 Ensure disabled state and help text when not available.

- [x] 7. Update dialog previews to use bytes (app/dialog/*)
  - [x] 7.1 In `resume_add_experience_dialog.py`, replace preview path usage with bytes from `ResumeService.render_preview`.
  - [x] 7.2 Repeat for `resume_add_education_dialog.py` and `resume_add_certificate_dialog.py`.
  - [x] 7.3 Verify previews re-render correctly after edits.

- [x] 8. Remove/deprecate PDF filename code paths
  - [x] 8.1 `grep` for `pdf_filename` and replace or remove usages across repo (UI, services, dialogs).
  - [x] 8.2 Add a deprecation note near `Resume.pdf_filename` in `src/database.py`: deprecated as of specs/008-resume_history; unused by runtime.
  - [x] 8.3 Ensure no writes/reads to `pdf_filename` remain; keep column for backward compatibility.

- [x] 9. One-off backfill script (temporary, not in VCS)
  - [x] 9.1 Write a local throwaway script to: iterate existing `Resume` rows and insert `ResumeVersion` v1 with `event_type='save'` and correct `template_name`/`resume_json`.
  - [x] 9.2 Do not set canonical during backfill; leave as unset.
  - [x] 9.3 Run locally once, validate by listing versions per job, then delete the script.
