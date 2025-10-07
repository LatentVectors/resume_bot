# Spec Tasks

## Tasks

- [x] 1. Update Database Schema for Cover Letters
  - [x] 1.1 Update `CoverLetter` table in `src/database.py`: remove `content` field, add `cover_letter_json: str` field, add `template_name: str` field (default "cover_000.html")
  - [x] 1.2 Create new `CoverLetterVersion` table in `src/database.py` with fields: `id`, `cover_letter_id` (FK), `job_id` (FK), `version_index`, `cover_letter_json`, `template_name`, `created_by_user_id`, `created_at`
  - [x] 1.3 Add appropriate indexes and constraints to `CoverLetterVersion` table for efficient querying
  - [x] 1.4 Verify SQLModel auto-migration will work correctly (test database startup)

- [x] 2. Create Cover Letter Feature Module Foundation
  - [x] 2.1 Create directory structure: `src/features/cover_letter/` with `__init__.py`
  - [x] 2.2 Create `src/features/cover_letter/types.py` with `CoverLetterData` Pydantic model (fields: name, title, email, phone, date, body_paragraphs) with validation (1-4 paragraphs, email format)
  - [x] 2.3 Create `src/features/cover_letter/content.py` with `DUMMY_COVER_LETTER_DATA` constant (single dummy profile: Jane Smith, Senior Software Engineer, with 3 placeholder paragraphs)
  - [x] 2.4 Create `src/features/cover_letter/validation.py` with `validate_template_minimal()` function that checks for required Jinja2 variables (name, email, date, body_paragraphs) and returns `(is_valid: bool, warnings: list[str])`

- [x] 3. Create Cover Letter Utils and Default Template
  - [x] 3.1 Create `src/features/cover_letter/utils.py` with utility functions: `list_available_templates()`, `convert_html_to_pdf()`, `render_template_to_html()` (mirror resume utils structure, reuse `get_template_environment()` from resume utils)
  - [x] 3.2 Create directory `src/features/cover_letter/templates/`
  - [x] 3.3 Create `src/features/cover_letter/templates/cover_000.html` - professional default template with business letter format, sender info, date, salutation, body paragraph loop, closing, professional fonts (Arial/Calibri), 1-inch margins, single-page constraint
  - [x] 3.4 Test `cover_000.html` renders correctly with `DUMMY_COVER_LETTER_DATA` using utils functions

- [x] 4. Implement LLM Template Generation for Cover Letters
  - [x] 4.1 Create `src/features/cover_letter/llm_template.py` with `generate_cover_letter_template_html()` function signature: `(user_text: str, current_html: str | None, image: bytes | None) -> str`
  - [x] 4.2 Develop LLM prompt emphasizing: single-page business letter format, professional hierarchy, proper spacing, margins (~1 inch), professional fonts, required Jinja2 variables
  - [x] 4.3 Implement function body similar to `src/features/resume/llm_template.py` structure, using same LLM model/configuration
  - [x] 4.4 Ensure function returns raw HTML (no markdown fences)
  - [x] 4.5 Test generation with sample user input and verify output passes validation

- [x] 5. Create CoverLetterTemplateService
  - [x] 5.1 Create `app/services/cover_letter_template_service.py` file with class structure
  - [x] 5.2 Import `TemplateVersion` model from `app/services/template_service.py`
  - [x] 5.3 Implement `generate_version()` method that calls `generate_cover_letter_template_html()`, validates template, renders preview using `DUMMY_COVER_LETTER_DATA`, returns `TemplateVersion` with html, pdf_bytes, warnings
  - [x] 5.4 Add error handling and logging for generation failures
  - [x] 5.5 Test service generates valid cover letter templates

- [x] 6. Create CoverLetterService with Versioning
  - [x] 6.1 Create `app/services/cover_letter_service.py` file with class structure
  - [x] 6.2 Implement versioning methods: `save_cover_letter()` (creates new version, updates canonical), `list_versions()` (ordered by version_index), `get_canonical()`, `pin_canonical()`
  - [x] 6.3 Implement data retrieval method: `get_cover_letter_for_job()`
  - [x] 6.4 Implement rendering method: `render_preview()` with session state caching (key: `cover_letter_pdf_cache`)
  - [x] 6.5 Implement utility method: `list_available_templates()`
  - [x] 6.6 Ensure `save_cover_letter()` updates `Job.has_cover_letter` flag and auto-increments version_index
  - [x] 6.7 Add comprehensive error handling and logging following `ResumeService` patterns

- [x] 7. Update Templates Page with Tab Structure
  - [x] 7.1 Modify `app/pages/templates.py`: add `st.segmented_control` with Resume and Cover Letter tabs, persist selection in `st.session_state["selected_template_tab"]`
  - [x] 7.2 Rename existing session state keys: `tmpl_chat_messages` → `resume_tmpl_chat_messages`, `tmpl_versions` → `resume_tmpl_versions`, `tmpl_selected_idx` → `resume_tmpl_selected_idx`, `tmpl_filename_input` → `resume_tmpl_filename_input`
  - [x] 7.3 Wrap existing resume template code in conditional block that renders when Resume tab selected
  - [x] 7.4 Create cover letter tab implementation: duplicate resume workflow structure with cover letter session state keys (`cover_tmpl_*`), use `CoverLetterTemplateService.generate_version()`, render with `DUMMY_COVER_LETTER_DATA`
  - [x] 7.5 Ensure download button uses filename pattern: `"cover_letter_template_{label}.html"`
  - [x] 7.6 Test tab switching preserves in-progress work in both tabs

- [x] 8. Implement Job Detail Cover Letter Tab - Layout and Form Inputs
  - [x] 8.1 Update `app/pages/job_tabs/cover.py`: replace placeholder with full implementation, add two-column 50/50 layout
  - [x] 8.2 Implement session state initialization: `cover_letter_draft`, `cover_letter_last_saved`, `cover_letter_dirty`, `cover_letter_template`, `cover_letter_template_saved`, `cover_letter_selected_version_id`, `cover_letter_loaded_from_version_id`
  - [x] 8.3 Implement initial load logic: pre-populate name/email/phone from user profile, set title from `job.job_title`, set date to current, set template to "cover_000.html"
  - [x] 8.4 Create left column inputs: text inputs for name, title, email, phone; date picker; single textarea (350px height) for body paragraphs with `"\n\n".join(body_paragraphs)` display and double-newline split on save
  - [x] 8.5 Add template selector dropdown listing templates from `src/features/cover_letter/templates/`
  - [x] 8.6 Implement read-only mode: when `job.applied_at` is set, disable all inputs, hide buttons, show info message
  - [x] 8.7 Test form inputs update session state correctly and handle missing profile data gracefully

- [x] 9. Implement Job Detail Cover Letter Tab - Versioning and Actions
  - [x] 9.1 Add version navigation controls to left column: ◀ ▶ buttons, version dropdown (descending order), pin button with `:material/keep:` icon
  - [x] 9.2 Implement version selection logic: default to canonical if exists else head, reload draft when version changes, keep draft when dirty
  - [x] 9.3 Implement right column: PDF preview using `CoverLetterService.render_preview()` with live updates, download button with proper filename pattern, disable preview if missing required fields
  - [x] 9.4 Implement Save button: calls `CoverLetterService.save_cover_letter()`, creates new version, updates session state, disabled when not dirty or missing name/email
  - [x] 9.5 Implement Discard button: reverts to last saved state, disabled when not dirty
  - [x] 9.6 Implement dirty state tracking: compare current draft JSON to last saved, enable/disable buttons accordingly
  - [x] 9.7 Add error handling: show warnings for missing profile data, missing templates, PDF rendering failures
  - [x] 9.8 Test complete versioning workflow: create, save, navigate, pin versions

- [x] 10. Add Filename Utility and Final Integration
  - [x] 10.1 Add `build_cover_letter_download_filename()` function to `app/shared/filenames.py` with signature `(company_name: str, job_title: str, full_name: str) -> str` returning pattern: `"CoverLetter - {company} - {title} - {name} - {yyyy_mm_dd}.pdf"`
  - [x] 10.2 Update job cover letter tab download button to use new filename function
  - [x] 10.3 Verify `app/pages/job.py` correctly renders cover letter tab (check if any updates needed for tab integration)
  - [x] 10.4 Test end-to-end workflow: create template on Templates page, create cover letter on job page, save multiple versions, navigate versions, pin canonical, download PDF
  - [x] 10.5 Test locked cover letter behavior when job.applied_at is set
  - [x] 10.6 Verify all acceptance criteria are met and error cases are handled
  - [x] 10.7 Run full application to ensure no regressions in existing functionality

