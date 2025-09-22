# Spec Tasks

## Tasks

- [x] 1. Update Pydantic models to use date types
  - [x] 1.1 Edit `src/features/resume/types.py` to set `ResumeExperience.start_date: date`
  - [x] 1.2 Edit `src/features/resume/types.py` to set `ResumeExperience.end_date: date | None`
  - [x] 1.3 Edit `src/features/resume/types.py` to set `ResumeEducation.grad_date: date`
  - [x] 1.4 Edit `src/features/resume/types.py` to set `ResumeCertification.date: date`
  - [x] 1.5 Ensure imports (`from datetime import date`) and type hints compile

- [x] 2. Remove string-based date formatting in data adapter
  - [x] 2.1 Delete `_format_date` from `src/features/resume/data_adapter.py`
  - [x] 2.2 Map `Education.grad_date` directly to `ResumeEducation.grad_date: date`
  - [x] 2.3 Map `Experience.start_date`/`end_date` directly to `ResumeExperience` fields
  - [x] 2.4 Keep `_format_phone` as-is; ensure `transform_user_to_resume_data` returns `date` types
  - [x] 2.5 Run a quick type check to ensure no callers expect strings

- [x] 3. Update rendering service contracts to accept ResumeData
  - [x] 3.1 Change `render_resume_pdf` signature to `(resume_data: ResumeData, template_name: str, dest_path: Path)` in `app/services/render_pdf.py`
  - [x] 3.2 Change `render_preview_pdf` signature to `(resume_data: ResumeData, template_name: str, preview_path: Path)`
  - [x] 3.3 Inside both, pass `resume_data.model_dump()` to the template renderer
  - [x] 3.4 Update imports and add necessary typing

- [x] 4. Update call sites to pass ResumeData to renderer
  - [x] 4.1 In `app/services/resume_service.py` `save_resume`, pass the `ResumeData` instance to `render_resume_pdf`
  - [x] 4.2 In `app/services/resume_service.py` `render_preview`, pass the `ResumeData` instance to `render_preview_pdf`
  - [x] 4.3 Persist with `resume_data.model_dump_json()` (remove extra re-validation)

- [x] 5. Migrate Resume tab UI to date objects
  - [x] 5.1 Remove `_parse_date` and `_format_date` from `app/pages/job_tabs/resume.py`
  - [x] 5.2 Bind `st.date_input` to `ResumeExperience.start_date: date`
  - [x] 5.3 Bind `st.date_input` to `ResumeExperience.end_date: date | None` (no clear button, no checkbox)
  - [x] 5.4 Bind `st.date_input` to `ResumeEducation.grad_date: date`
  - [x] 5.5 Bind `st.date_input` to `ResumeCertification.date: date`
  - [x] 5.6 Ensure updated models write `date`/`None` directly

- [x] 6. Update all templates for inline date formatting
  - [x] 6.1 Edit `src/features/resume/templates/resume_000.html` to use `strftime('%b %Y')` and show `Present`
  - [x] 6.2 Repeat formatting for `resume_001.html` through `resume_006.html`
  - [x] 6.3 Verify no template expects pre-formatted strings

- [x] 7. Agent boundary adjustments
  - [x] 7.1 Ensure agent entry points accept and pass `ResumeData` without pre-converting dates
  - [x] 7.2 Confirm resume-to-string formatter converts `date` fields to strings as needed

- [x] 8. Clean up legacy date parsing/formatting
  - [x] 8.1 Grep for remaining helpers handling `"Present"` or `Mon YYYY` outside templates and remove/update
  - [x] 8.2 Remove any unused imports/constants tied to string date handling
