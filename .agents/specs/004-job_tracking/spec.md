### Jobs & Job Tracking – Phase 004 (Comprehensive Spec)

## 1) Purpose and Motivation
- Problem: The current app generates resumes from a single home flow and lists them in a basic Jobs table. It lacks a structured way to track the full lifecycle of a job application (from saving to applying to interviewing), associate multiple artifacts (resume, cover letter, messages, application responses), and preserve immutable history once applied.
- Goal: Introduce first-class job tracking with a robust information architecture, navigable detail pages, status/favorite management, artifact scaffolding, and a Save Job intake flow that seeds jobs from a raw description. This enables future sprints to progressively enhance each content area while today we establish a durable foundation.
- Outcomes: Clear “source of truth” for jobs and related artifacts; predictable navigation with deep links; locking for applied jobs to protect historical accuracy; index-level visibility and filtering for prioritization.

## 2) User Experience Overview (Narrative)
1. A user pastes a description on Home and clicks “Save Job”. The app uses an LLM to extract Title and Company and pre-populates a dialog. The user completes required fields, optionally favorites the job, and saves.
2. The app redirects to a hidden Job Detail page (`_job.py?job_id=...`) showing an Overview tab and placeholders for Resume, Cover Letter, Responses, and Messages. The Overview displays a concise summary of the job description and key job metadata with simple actions.
3. From the Jobs index, the user sees all jobs sorted by created date with filters for status and a favorites toggle. Each row indicates whether Resume or Cover Letter content exists. Clicking View opens the same detail page via query param.
4. When the user changes the status to Applied, the system fixes `applied_at` and locks the job-linked Resume, Cover Letter, and Response artifacts so their content remains immutable. Messages lock only when sent.
5. Over time, users can attach notes, draft cover letters or messages (future), and manage responses—scoped to jobs or global (via Responses page). This phase scaffolds the models and UI structure without implementing advanced editors.

## 3) Scope of This Phase
- Implement a Save Job flow on Home (with LLM extraction) and redirect to the Job Detail page after saving.
- Create a hidden Job Detail page using query params; render Overview with edit/save for title/company, status dropdown, favorite toggle, description expand/collapse, and quick actions.
- Revamp Jobs index with filters (status multiselect; favorites toggle), required columns, and view navigation.
- Add minimal placeholder tables for Resume, CoverLetter, Message, Response, and Note with locking semantics wired to status changes.
- Do not implement advanced content authoring or cover letter PDF rendering; placeholders only.

Out of scope in this phase: bulk response generation, advanced editors for resume/cover letter/messages, PDF rendering for cover letters, complex styling, scroll restoration guarantees.

## 4) Information Architecture & Navigation
- Pages
  - `app/pages/home.py` – adds Save Job flow.
  - `app/pages/jobs.py` – index with filters and columns; “View” navigates via param.
  - `app/pages/_job.py` – hidden detail page, accessed via `?job_id=123`, not linked in sidebar.
  - `app/pages/responses.py` – global Responses index (sidebar) to manage manual responses.
- Deep Links
  - Jobs Detail: `_job.py?job_id={id}`. Unknown IDs show an error with navigation back to Jobs.
- Filter Memory
  - Persist index filters in query params. Scroll position restoration is best-effort and not guaranteed.

## 5) Data Model (Authoritative)
All tables use `SQLModel` with `created_at` and `updated_at` populated server-side. New tables are intentionally minimal to enable wiring and future extension.

### 5.1 Job (existing; add fields)
- id: int PK
- user_id: int FK -> User
- job_description: str
- company_name: str | None
- job_title: str | None
- resume_filename: str  // keep for now; still used for viewing/downloading PDFs
- status: Literal["Saved","Applied","Interviewing","Not Selected","No Offer","Hired"] (default "Saved")
- is_favorite: bool (default False)
- applied_at: datetime | None  // set only the first time status becomes Applied
- has_resume: bool (default False)
- has_cover_letter: bool (default False)
- created_at: datetime
- updated_at: datetime

Notes
- `has_resume` / `has_cover_letter` are denormalized booleans to simplify index rendering. Keep consistent when creating/deleting child artifacts.
- Default ordering on index: `created_at` desc.

### 5.2 Resume (new, placeholder)
- id: int PK
- job_id: int FK -> Job
- pdf_filename: str
- locked: bool (default False)
- created_at: datetime
- updated_at: datetime

Notes
- `Job.resume_filename` remains the source of truth for viewing. `Resume` exists as scaffolding; migration will move the filename to this table in a future sprint.

### 5.3 CoverLetter (new, placeholder)
- id: int PK
- job_id: int FK -> Job
- content: str  // plain text for now
- locked: bool (default False)
- created_at: datetime
- updated_at: datetime

Notes
- No UI to create cover letters in this phase. Reserve `data/cover_letters/{cover_letter_id}.pdf` for future rendering; no files created now.

### 5.4 Message (new, minimal)
- id: int PK
- job_id: int FK -> Job
- channel: Literal["email","linkedin"]
- body: str
- sent_at: datetime | None
- locked: bool  // becomes True when `sent_at` is set
- created_at: datetime
- updated_at: datetime

### 5.5 Response (new, minimal)
- id: int PK
- job_id: int | None FK -> Job
- prompt: str
- response: str
- source: Literal["manual","application"]
- ignore: bool (default False)
- locked: bool (default False)  // set True when related Job becomes Applied
- created_at: datetime
- updated_at: datetime

### 5.6 Note (new, minimal)
- id: int PK
- job_id: int FK -> Job
- content: str
- created_at: datetime
- updated_at: datetime

## 6) State Transitions & Locking Semantics
- Status Enum: `Saved` (default) → `Applied` → `Interviewing` → terminal paths: `Hired`, `Not Selected`, `No Offer`. Back-and-forth transitions are allowed; `applied_at` is set only on the first transition to `Applied` and never changed.
- On first transition to `Applied`:
  - Set `applied_at` if null.
  - Lock all `Resume`, `CoverLetter`, and `Response` rows linked to the job (`locked=True`).
- Messages
  - Lock when `sent_at` is set, independent of job status.
- Notes
  - Remain editable/deletable in this phase.

## 7) Home – Save Job Flow
- UI
  - Input label changed to “Job Description”.
  - Add “Save Job” button left of “Generate Resume”.
- Behavior
  - On click, call `extract_title_company(text)` using `gpt-3.5-turbo`.
  - Open a dialog with fields: Title (required), Company (required), Favorite toggle, Job Description (required, editable). Save disabled until required fields are non-empty.
  - On Save: create Job with `status="Saved"`, set denorm flags to False, and redirect to `_job.py?job_id=...`.
  - If extraction fails/returns `None` values, leave fields blank; user must fill them in.
- Services & Functions
  - `src/features/jobs/extraction.py`
    - Pydantic model: `TitleCompany(title: str | None, company: str | None)`
    - `extract_title_company(text: str) -> TitleCompany` using `OpenAIModels.gpt_3_5_turbo` and a simple structured-output prompt.
  - `app/services/job_service.py`
    - `save_job_with_extraction(description: str, favorite: bool) -> DbJob`

## 8) Jobs Index – UX & Behavior
- Filters
  - Status multiselect: default to `Saved`, `Applied`, `Interviewing`.
  - Favorites toggle: off by default (shows all).
- Columns
  - `Title | Company | Status | Created | Applied | Favorite | Resume | Cover Letter`
  - Status pills with colors:
    - Saved: gray; Applied: green outline; Interviewing: green filled; Not Selected: red outline; No Offer: red filled; Hired: green filled.
  - Resume and Cover Letter: boolean columns reflecting `has_resume` / `has_cover_letter`.
- Sorting
  - Default: `created_at` desc.
- Actions
  - “View” navigates to `_job.py?job_id={id}`

## 9) Job Detail – UX & Behavior (`_job.py`)
- Tabs: Overview | Resume | Cover Letter | Responses | Messages (with simple circle badges: solid if content exists; outline if not).
- Overview
  - Description: expandable; show first 500 chars collapsed with option to expand fully.
  - Title & Company: read-only until “Edit”; then inline edit with “Save”.
  - Status: dropdown with enum; handles transition effects (applied_at set, locking, flags unaffected).
  - Favorite: toggle.
  - Quick Actions (right column):
    - Download Resume PDF: enabled if `resume_filename` present and file exists.
    - Cover Letter: Download / Copy disabled (placeholders).
    - New Message: opens dialog with `channel` and `body` fields; saves Message; sets `locked` if user marks sent (future); for now, creation only and unlocked.
- Other tabs: placeholders only; no editing flows in this sprint.

## 10) Error Handling & Empty States
- Missing resume file: disable download and show inline message.
- Unknown job id in detail page: show error and link to Jobs index.
- LLM extraction error: log, open dialog with empty fields, and continue.
- No jobs: Jobs index shows guidance to create a job from Home.

## 11) Configuration & Models
- Use `OpenAIModels.gpt_3_5_turbo` for extraction (already present in `src/core/models.py`).
- No new external dependencies required.

## 12) Migration Plan
1. Add columns to `Job`: `status` (default `Saved`), `is_favorite` (default `False`), `applied_at` (nullable), `has_resume` (default `False`), `has_cover_letter` (default `False`).
2. Create new tables: `Resume`, `CoverLetter`, `Message`, `Response`, `Note`.
3. Backfill existing `Job` rows:
   - `status = "Saved"`, `is_favorite = False`, `applied_at = NULL`, `has_resume = (resume_filename IS NOT NULL)`, `has_cover_letter = False`.
4. Verify `jobs.py` logic continues to support legacy records.

## 13) Implementation Notes
- Architecture & Responsibilities
  - `app/pages/*` and `app/dialog/*`: UI only. Handle layout, widgets, simple view-state, reading user input, and rendering success/error messages. Keep these modules thin; avoid business rules, DB calls, or LLM calls here.
  - `app/services/*`: Business logic and IO. Centralize interactions with `src/database.db_manager`, locking rules, denormalized flag updates, validation, and LLM calls via `src/core/models.get_model`. Expose clear, typed methods that pages/dialogs call.
  - Prohibition: Do not call `db_manager` directly from `app/pages` or `app/dialog`. All reads/writes must flow through services. This keeps UI uncluttered and testable.
  - Examples
    - Home Save Job: `JobService.save_job_with_extraction(description: str, favorite: bool) -> DbJob` encapsulates LLM extraction + Job creation + redirects (UI triggers navigation).
    - Jobs Index: `JobService.list_jobs(user_id, statuses, favorites_only)` returns view models or DB rows; UI formats the table without extra business logic.
    - Job Detail: `JobService.get_job(job_id)`, `JobService.update_job_fields(job_id, {title, company, is_favorite})`, `JobService.set_status(job_id, status)` (applies `Applied` side-effects and locking), `JobService.add_note(job_id, content)`, `JobService.create_message(job_id, channel, body)`.
  - Domain helpers under `src/features/*` are allowed for reusable logic (e.g., extraction), but UI should still access them through services to keep a consistent boundary.
- Keep denorm flags (`has_*`) in sync on create/delete of child rows.
- Prefer helper methods in a `JobService` to change status and apply locking in one place.
- Use `st.query_params` for filter state; avoid complex front-end state.
- Follow existing logging and error patterns.

## 14) Acceptance Criteria (Testable)
1. Home Save Job
   - “Job Description” label, “Save Job” button present.
   - Dialog opens with extracted Title/Company when possible; Save disabled until required fields are filled.
   - On Save, new Job is created with defaults and user is redirected to `_job.py?job_id=...`.
2. Jobs Index
   - Filters present; default statuses selected (Saved, Applied, Interviewing); favorites toggle off.
   - Columns exactly: Title | Company | Status | Created | Applied | Favorite | Resume | Cover Letter.
   - Sorted by created desc; View navigates to detail.
3. Job Detail
   - Overview renders description with expand, edit/save for Title/Company, status dropdown, favorite toggle.
   - Quick actions: Resume download only when file exists; Cover Letter actions disabled.
   - Tabs show circle badges; bodies are placeholders.
4. Locking
   - First change to Applied sets `applied_at` and locks Resume/CoverLetter/linked Responses.
   - Message locks only when `sent_at` is set.
5. Data
   - New tables exist with specified columns; Job has added columns; backfill defaults applied.

## 15) Future Work (Next Sprints)
- Resume tab with versioning and migration of `resume_filename` into `Resume` table.
- Cover Letter authoring and PDF rendering under `data/cover_letters/`.
- Messages sending workflows and channel-specific fields (subject, recipients, etc.).
- Responses bulk generation, tagging, and richer filters.
- Improved state persistence and visual indicators; iconography beyond circles/booleans.

