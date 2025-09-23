## Sprint: Resume Version History and Canonical Pinning (specs/008-resume_history)

### Overview
- Persist every resume version per job and allow navigation across versions.
- Introduce a single canonical version set explicitly via a pin icon.
- Stop persisting PDFs; render previews/downloads on-the-fly in memory.
- Older versions remain editable; edits create a new head version.
- Applied jobs are fully locked to canonical only (only view/download canonical).

### Out of Scope
- Multi-user concurrency handling beyond current single-user assumption.
- Template authoring/management changes beyond adding bytes-based rendering.

## User Stories
- As a user, when I click Generate, a new version v{N+1} is created and becomes the selected head; canonical is unchanged.
- As a user, when I click Save, a new version v{N+1} is created and becomes the selected head; canonical is unchanged.
- As a user, I can navigate versions via < | v# | >; the editor shows the selected version and is editable even for older versions.
- As a user, clicking the pin sets the selected version as canonical and shows a confirmation toast.
- As a user, when job status is Applied, I can only view/download the canonical version; navigation and editing are disabled.
- As a user, I can only download when the selected version is canonical and the editor is clean (not dirty).

## Data Model
### New Entities (in `src/database.py`)
- `ResumeVersionEvent` (StrEnum): 'generate' | 'save' | 'reset'.
- `ResumeVersion` (SQLModel, table=True):
  - `id: int | None` (PK)
  - `job_id: int` (FK `job.id`)
  - `version_index: int` (monotonic per job starting at 1)
  - `parent_version_id: int | None`
  - `event_type: ResumeVersionEvent`
  - `template_name: str`
  - `resume_json: str`
  - `created_by_user_id: int`
  - `created_at: datetime = now()`
  - Constraints: Unique `(job_id, version_index)`; Index `(job_id, created_at desc)`

### Existing Entities
- `Resume` remains the canonical snapshot for the job (JSON + template). Do NOT store or rely on `pdf_filename` anymore. Add a deprecation note in code that `pdf_filename` is deprecated as of `specs/008-resume_history` and should not be written or read in runtime logic.
- `Job.has_resume`: True only if a canonical `Resume` row exists for the job. It does NOT depend on PDFs.

## Behaviors and Workflows
### Version Creation Triggers
- Generate → create `ResumeVersion` with `event_type='generate'`; select as head; do not change canonical.
- Save → create `ResumeVersion` with `event_type='save'`; select as head; do not change canonical.
- Reset → create a new head version with `event_type='reset'` seeded from profile; clear canonical; do not delete history.

### Navigation and Selection
- Header controls (right-aligned): `< | dropdown | >` where the dropdown lists simple labels `v#` (starting at v1).
- The selected version is loaded into the editor; older versions are editable. Any Generate/Save from an older version creates a new head.
- Pin icon to the right of the controls: filled when the selected version is canonical, outlined otherwise. One-click pin updates canonical and shows a toast.
- Bounds: `<` disabled at oldest; `>` disabled at head.

### Canonical Rules
- Canonical changes only via pin; not by Generate/Save.
- On page load, select canonical if set; else select the head (latest) version.
- Applied state: only the canonical is visible and downloadable; navigation, Generate, Save, and Pin are disabled/hidden.

### Preview and Download
- PDFs are rendered on-the-fly in memory (bytes). No file writes to disk for preview or download.
- Download is enabled only when the selected version is canonical AND the editor state is clean (not dirty). Non-canonical or dirty drafts cannot be downloaded.

## Services and APIs
All type annotations required; follow project code style rules.

### `app/services/resume_service.py`
- Add:
  - `create_version(job_id: int, resume_data: ResumeData, template_name: str, event_type: ResumeVersionEvent, parent_version_id: int | None = None) -> DbResumeVersion`
  - `list_versions(job_id: int) -> list[DbResumeVersion]`
  - `get_version(version_id: int) -> DbResumeVersion | None`
  - `pin_canonical(job_id: int, version_id: int) -> DbResume` (writes canonical JSON/template to `Resume`)
  - `get_canonical(job_id: int) -> DbResume | None`
- Update:
  - `generate_resume_for_job(...)`: after computing updated draft, call `create_version(..., 'generate')`; return updated draft; do not touch canonical.
  - `save_resume(...)`: create version with `event_type='save'`; do not touch canonical; return newly persisted `ResumeVersion` or the prior return type as appropriate.
  - `render_preview(...)`: return `(pdf_bytes: bytes)` rather than writing a preview file.

### `app/services/render_pdf.py`
- Add bytes-based functions (no disk I/O):
  - `render_resume_pdf_bytes(resume_data: ResumeData, template_name: str) -> bytes`
  - `render_preview_pdf_bytes(resume_data: ResumeData, template_name: str) -> bytes` (may delegate to same implementation)

### `src/features/resume/utils.py`
- Add `render_template_to_pdf_bytes(template_name: str, context: dict, templates_dir: Path) -> bytes`.

### `app/services/job_service.py`
- In `refresh_denorm_flags`: compute `has_resume` as True iff a `Resume` row exists; remove all reliance on `pdf_filename`.

## UI: `app/pages/job_tabs/resume.py`
- Add right-aligned header controls `< | dropdown | >` and pin icon; maintain selected version and canonical state in session.
- Remove all logic that reads/writes `pdf_filename` or reads PDFs from disk.
- Replace preview embedding to accept PDF bytes (e.g., `_embed_pdf_bytes(pdf_bytes)`).
- Enforce download rules: only enabled if canonical selected AND editor clean.
- Editable history: older versions are fully editable; actions create a new head.
- Applied state: show canonical preview/download only; hide navigation and editing controls, including pin.

## Other Pages
- `app/pages/job_tabs/overview.py`: remove `pdf_filename` usage; download button only for canonical + clean; fetch PDF bytes via service.
- Dialogs: `app/dialog/resume_add_experience_dialog.py`, `app/dialog/resume_add_education_dialog.py`, `app/dialog/resume_add_certificate_dialog.py`: update preview to use bytes from `ResumeService.render_preview`.

## Backfill (one-time)
- Purpose: populate initial `ResumeVersion` history from existing `Resume` rows.
- Action: for each existing `Resume`, create a single `ResumeVersion` with `event_type='save'` and `version_index=1` using the row's `resume_json` and `template_name`.
- Do not set canonical during backfill (canonical remains unset until user pins). As a result, `Job.has_resume` remains false until a pin occurs.
- Execution: run via a temporary, one-off script executed manually and NOT committed to version control; discard after use.

## Filepaths to Add/Edit/Delete
- Add (data model): `src/database.py` (new `ResumeVersionEvent`, `ResumeVersion`).
- Add (helpers): `render_template_to_pdf_bytes` in `src/features/resume/utils.py`.
- Add (render bytes): new functions in `app/services/render_pdf.py`.
- Update (service): `app/services/resume_service.py` (new version APIs; no canonical writes on save/generate; bytes preview).
- Update (service): `app/services/job_service.py` (`refresh_denorm_flags` to use presence of canonical `Resume`).
- Update (UI): `app/pages/job_tabs/resume.py` (controls, pin, in-memory preview/download, applied lock, remove `pdf_filename`).
- Update (UI): `app/pages/job_tabs/overview.py` (remove `pdf_filename`, canonical-only download, in-memory rendering).
- Update (dialogs): `app/dialog/resume_add_experience_dialog.py`, `app/dialog/resume_add_education_dialog.py`, `app/dialog/resume_add_certificate_dialog.py` (use bytes preview).
- Delete/Deprecate: any code paths that write/read `pdf_filename`; leave the DB column but annotate as deprecated. Do not remove DB column in this sprint.

## Acceptance Criteria
- Data model
  - `ResumeVersion` table exists with unique `(job_id, version_index)` and index `(job_id, created_at desc)`.
  - `ResumeVersionEvent` is a StrEnum with values 'generate' | 'save' | 'reset'.
  - `Job.has_resume` reflects existence of canonical `Resume` only.
- Services
  - Generate/Save create exactly one `ResumeVersion` with correct `event_type` and incremented `version_index`.
  - Pin writes canonical JSON/template to `Resume` and sets `has_resume=True`.
  - No code writes or depends on `pdf_filename` at runtime.
  - Preview/download return bytes; no file I/O for PDFs.
- UI
  - `<`/`>` disabled at bounds; dropdown shows `v1..vN`.
  - Pin shows filled when canonical selected; outline otherwise; one-click updates canonical with toast.
  - Applied: only canonical visible and downloadable; navigation/editing/pin disabled.
  - Download enabled only when selected is canonical and editor clean; disabled otherwise.
- Backfill
  - One-off script creates `v1` for each existing `Resume`; does not set canonical.

## Risks, Dependencies, Assumptions
- Risks
  - In-memory PDF rendering performance on large resumes may cause UI delays.
  - Residual references to `pdf_filename` could break UI if not removed.
- Dependencies
  - PDF renderer supports returning bytes reliably.
  - Streamlit PDF viewer component supports bytes input consistently across browsers.
- Assumptions
  - Single-user environment; no concurrent edits of the same job.
  - Unlimited version history is acceptable for local storage.

## Rationale
- Removing persisted PDFs avoids stale file management and simplifies state; all PDFs are deterministic from data + template.
- Explicit pinning gives the user control over canonical selection independent of recent edits.
- Editable history enables quick experiments while preserving a linear, navigable history.

## Test Plan
- Unit
  - `create_version` sets correct fields and increments `version_index`; uniqueness enforced.
  - `pin_canonical` updates canonical and flips `Job.has_resume`.
  - Download guard logic (canonical + clean) enables/disables appropriately.
- Integration
  - Generate → Save → Pin results in correct head/canonical separation and navigation bounds.
  - Applied state hides navigation/editing and allows only canonical preview/download.
  - Reset creates `reset` version, clears canonical, preserves prior versions.
- Regression
  - No disk I/O for previews/downloads; `pdf_filename` is not written/read.


