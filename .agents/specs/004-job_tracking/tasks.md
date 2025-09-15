# Spec Tasks

## Tasks

- [x] 1. Add database models and Job fields (SQLModel)
  - [x] 1.1 Extend `Job` with `status`, `is_favorite`, `applied_at`, `has_resume`, `has_cover_letter`, timestamps
  - [x] 1.2 Create `Resume`, `CoverLetter`, `Message`, `Response`, `Note` SQLModel tables with timestamps and defaults
  - [x] 1.3 Ensure `Message.locked` derives from `sent_at` (True when set) and others have explicit `locked`
  - [x] 1.4 Register models with the existing DB manager and metadata so tables are created
  - [x] 1.5 Add helpers to consistently set `created_at`/`updated_at`

- [x] 2. Create extraction module for Title/Company
  - [x] 2.1 Add `src/features/jobs/__init__.py` and `src/features/jobs/extraction.py`
  - [x] 2.2 Define Pydantic `TitleCompany` with `title: str | None`, `company: str | None`
  - [x] 2.3 Implement `extract_title_company(text)` using `OpenAIModels.gpt_3_5_turbo` with structured output
  - [x] 2.4 Log and return `None` fields on model failure without raising to UI

- [x] 3. Implement `JobService` in `app/services/job_service.py`
  - [x] 3.1 `save_job_with_extraction(description: str, favorite: bool) -> DbJob`
  - [x] 3.2 `list_jobs(user_id, statuses, favorites_only)` with default sorting by `created_at` desc
  - [x] 3.3 `get_job(job_id)` and `update_job_fields(job_id, {title, company, is_favorite})`
  - [x] 3.4 `set_status(job_id, status)` applying first-time `Applied` side-effects (`applied_at`, locking)
  - [x] 3.5 `create_message(job_id, channel, body)` and `add_note(job_id, content)`
  - [x] 3.6 Keep denorm flags (`has_resume`, `has_cover_letter`) in sync when child rows created/deleted

- [x] 4. Home page: Save Job intake flow
  - [x] 4.1 Change input label to “Job Description” in `app/pages/home.py`
  - [x] 4.2 Add a “Save Job” button (left of Generate Resume) invoking extraction + dialog
  - [x] 4.3 Create `app/dialog/job_save_dialog.py` to capture Title, Company, Favorite, Description
  - [x] 4.4 Disable Save until required fields present; handle empty extraction results
  - [x] 4.5 On save, call `JobService.save_job_with_extraction` and redirect to `_job.py?job_id=...`

- [x] 5. Jobs index revamp in `app/pages/jobs.py`
  - [x] 5.1 Add filters: status multiselect (default Saved/Applied/Interviewing) and favorites toggle
  - [x] 5.2 Persist filters in query params; default sort by `created_at` desc
  - [x] 5.3 Columns: Title | Company | Status | Created | Applied | Favorite | Resume | Cover Letter
  - [x] 5.4 Render status pills with specified colors; boolean columns from denorm flags
  - [x] 5.5 Add View action to navigate to `_job.py?job_id={id}`

- [x] 6. Hidden Job Detail page `_job.py`
  - [x] 6.1 Read `job_id` from query params; show error + link to Jobs if unknown
  - [x] 6.2 Tabs: Overview | Resume | Cover Letter | Responses | Messages with circle badges
  - [x] 6.3 Overview: description expand/collapse (first 500 chars collapsed)
  - [x] 6.4 Inline edit/save for Title/Company; Favorite toggle; Status dropdown wired to `JobService.set_status`
  - [x] 6.5 Quick actions: Resume PDF download enabled only when file exists; Cover Letter actions disabled

- [x] 7. Global Responses index page
  - [x] 7.1 Add `app/pages/responses.py` to list `Response` rows with minimal fields
  - [x] 7.2 Provide basic filter for `ignore` and `source`; link to Job when `job_id` is present
  - [x] 7.3 Add to sidebar navigation

- [x] 8. Artifact scaffolding and locking semantics
  - [x] 8.1 Ensure first transition to Applied sets `applied_at` only once
  - [x] 8.2 Lock `Resume`, `CoverLetter`, and `Response` for the job on first Applied
  - [x] 8.3 Lock `Message` when `sent_at` is set; independent of job status
  - [x] 8.4 Make status transitions idempotent and reversible (except `applied_at` remains first-set)

- [x] 9. Denormalized flags management
  - [x] 9.1 On create/delete of `Resume`/`CoverLetter`, update `Job.has_resume`/`has_cover_letter`
  - [x] 9.2 Reflect flags correctly in Jobs index and Job Detail badges
  - [x] 9.3 Add lightweight helpers in `JobService` to keep flags consistent
