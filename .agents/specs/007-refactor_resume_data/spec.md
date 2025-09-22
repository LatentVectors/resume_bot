# Sprint 007: Refactor Resume Data to Use Date Objects and Tighten Contracts

## Overview
This sprint standardizes all resume date fields as Python `date` objects, tightens type contracts to require `ResumeData` where appropriate, and moves all date string formatting into Jinja templates at render-time. The goal is to simplify UI and services by eliminating ad-hoc string parsing, ensure consistent ISO serialization to the database, and provide unambiguous rendering rules across all resume templates.

Key outcomes:
- All resume date fields use `date` / `date | None` in Pydantic models.
- Database persistence uses Pydantic ISO serialization via `model_dump_json()`; reads hydrate with `ResumeData.model_validate_json()`.
- Rendering functions accept `ResumeData`; templates format dates to `Mon YYYY` and show the literal word "Present" when appropriate.
- Legacy string-based date parsing/formatting helpers are removed from adapters and UI.

## User Stories
- As a user, I can edit resume dates using native date pickers. If I leave an end date blank, it is treated as an ongoing role and displayed as "Present" in the PDF.
- As a user, I can preview and save resumes where all dates render consistently as `Mon YYYY` across experience, education, and certifications.

## Data Model Updates
File: `src/features/resume/types.py`
- Update Pydantic models:
  - `ResumeExperience.start_date: date`
  - `ResumeExperience.end_date: date | None`
  - `ResumeEducation.grad_date: date`
  - `ResumeCertification.date: date`
- Keep other fields unchanged.
- Rationale: Using concrete date types simplifies UI integration (date pickers), prevents invalid string states, and leverages Pydantic’s ISO serialization.

## Serialization and Hydration
- Writes: `resume_data.model_dump_json()` persists ISO date strings (YYYY-MM-DD) to DB column `resume_json`.
- Reads: `ResumeData.model_validate_json(db_row.resume_json)` hydrates ISO strings to Python `date` objects.
- Applies to all flows that write/read the `ResumeData` JSON.

## Services and Rendering Contracts
Files: `app/services/render_pdf.py`, `app/services/resume_service.py`
- Rendering functions must accept `ResumeData`; convert to dict at render-time for template context:
  - `render_resume_pdf(resume_data: ResumeData, template_name: str, dest_path: Path) -> Path`
  - `render_preview_pdf(resume_data: ResumeData, template_name: str, preview_path: Path) -> Path`
- Inside the renderer, pass `resume_data.model_dump()` so templates can access `date` objects and call `strftime`.
- `ResumeService.save_resume` persists with `resume_data.model_dump_json()` and invokes `render_resume_pdf(resume_data, template_name, output_path)`.
- `ResumeService.render_preview` calls `render_preview_pdf(resume_data, template_name, preview_path)`.

## Data Adapter Changes
File: `src/features/resume/data_adapter.py`
- Delete `_format_date` and any string formatting of dates.
- Map DB date columns directly to `date` fields on models:
  - Education: `grad_date = edu.grad_date`
  - Experience: `start_date = exp.start_date`, `end_date = exp.end_date` (nullable)
- Keep `_format_phone` unchanged.
- Ensure `transform_user_to_resume_data()` returns `ResumeData` with `date` types.

## UI Updates (Resume Tab)
File: `app/pages/job_tabs/resume.py`
- Remove string date parsing/formatting helpers (e.g., `_parse_date`, `_format_date`).
- Experience section:
  - `start_date`: `st.date_input` bound to `exp.start_date` (a `date`).
  - `end_date`: `st.date_input` bound to `exp.end_date` (a `date | None`). No checkbox and no separate clear button; the user clears the date directly in the widget to set `None`.
- Education: `st.date_input` bound to `edu.grad_date` (a `date`).
- Certifications: `st.date_input` bound to `cert.date` (a `date`).
- When saving back to the model, write `date` objects (or `None`) directly.

## Templates
Directory: `src/features/resume/templates/*.html` (default `resume_000.html`)
- Update all templates to perform inline date formatting and "Present" handling.
- Experience example:
  - `{{ exp.start_date.strftime('%b %Y') }} – {{ exp.end_date.strftime('%b %Y') if exp.end_date else 'Present' }}`
- Education example:
  - `{{ edu.grad_date.strftime('%b %Y') }}`
- Certification example:
  - `{{ cert.date.strftime('%b %Y') }}`
- Locale: Use English (US) defaults. Month names via `%b`. Literal ongoing role label: `Present`.

## Agent Boundary
- Pass the full `ResumeData` object to the agent.
- Any function that formats resume content to a string is responsible for converting `date` fields to strings.
- Do not pre-convert dates to strings before passing to the agent.

## Impacted Files
- `src/features/resume/types.py`
- `src/features/resume/data_adapter.py`
- `src/features/resume/templates/*.html`
- `app/services/render_pdf.py`
- `app/services/resume_service.py`
- `app/pages/job_tabs/resume.py`

## Acceptance Criteria (Manual QA)
- Experiences: start/end use date pickers; deleting end date results in `end_date = None` and renders as `Present`.
- Education/Certifications: dates captured via date pickers and persisted as `date`.
- Persistence: DB `resume_json` stores ISO date strings; reading hydrates to `date` via `ResumeData.model_validate_json()`.
- Rendering: Services accept `ResumeData`; templates format with `strftime('%b %Y')` and show `Present` when `end_date` is `None`.
- All seven templates render correct date formats; no template expects pre-formatted strings.
- All legacy date parsing/formatting helpers removed; no handling for values like `"Present"` or `"Mon YYYY"` outside templates.
- Downloaded PDFs display correct date formats across Experience, Education, and Certifications.

## Risks, Dependencies, Assumptions
- Risk: Any template still expecting string dates may render incorrectly; mitigate by updating all templates in one pass and verifying.
- Dependency: Pydantic ISO serialization for `date` (default behavior) is relied upon.
- Assumption: Agent pipelines accept `ResumeData` with `date` fields; formatter functions convert to strings as needed.

## Out of Scope
- Automated migrations: Not required for this sprint.
- DB reset automation: Will be performed manually; no reset script included.
- Test automation: Manual QA only for this sprint.

## Rationale
- Using `date` fields improves correctness and simplifies UI date handling.
- Centralizing formatting in templates avoids duplicated and inconsistent string logic.
- Tightened type contracts (`ResumeData` required) reduce ambiguity and runtime errors.
