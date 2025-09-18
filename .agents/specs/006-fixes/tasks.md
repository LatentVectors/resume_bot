# Spec Tasks

## Tasks

 - [x] 1. Update database models to align with ResumeData
  - [x] 1.1 Edit `src/database.py`: add `location: str | None = Field(default=None)` to `Experience`.
  - [x] 1.2 Replace `Education` fields with `institution: str`, `degree: str`, `major: str`, `grad_date: date`.
  - [x] 1.3 Add new `Certification` model with fields from spec (id, user_id, title, institution?, date, created_at, updated_at).
  - [x] 1.4 Ensure imports for `date`/`datetime` and `Field` are correct and consistent.
  - [x] 1.5 Remove/avoid any legacy education start/end date references in this file.
  - [x] 1.6 Delete the SQLite DB file locally to recreate schema on next run.

- [x] 2. Create shared UI foundations: constants and components
  - [x] 2.1 Add `app/constants.py` exporting `MIN_DATE = date(1950, 1, 1)`.
  - [x] 2.2 Add `app/components/status_badge.py` with `render_status_badge(status: str)` using a consistent color/icon mapping.
  - [x] 2.3 Add `app/components/confirm_delete.py` exposing `confirm_delete(entity_label, on_confirm, on_cancel)` with primary Delete and secondary Cancel.
  - [x] 2.4 Keep components free of page-specific logic; importable from Jobs/Profile pages.

- [x] 3. Update Experience and Education services
  - [x] 3.1 In `app/services/experience_service.py`, accept/persist optional `location` on create/update.
  - [x] 3.2 In `app/services/education_service.py`, switch to `institution/degree/major/grad_date` validation and persistence.
  - [x] 3.3 Maintain existing error handling patterns; ensure date parsing unaffected.
  - [x] 3.4 Add/adjust small helper methods if needed to reduce duplication.

- [x] 4. Add CertificateService
  - [x] 4.1 Create `app/services/certificate_service.py` with CRUD APIs for `Certification`.
  - [x] 4.2 Mirror validation/logging patterns from Experience/Education services.
  - [x] 4.3 Ensure service returns domain objects/dicts consistent with existing services.

- [x] 5. Resume data adapter field alignment
  - [x] 5.1 Update `src/features/resume/data_adapter.py` to map DB → `ResumeData` with `Education(institution, degree, major, grad_date)`.
  - [x] 5.2 Include `Experience.location` when transforming experience items.
  - [x] 5.3 Verify output structure matches `src/features/resume/types.py`.

- [x] 6. Rename Profile page module and update navigation
  - [x] 6.1 Rename `app/pages/user.py` → `app/pages/profile.py`.
  - [x] 6.2 In `app/main.py`, register `st.Page("pages/profile.py", title="Profile", icon=":material/person:")`.
  - [x] 6.3 Update any `st.switch_page`/`st.page_link` references to `pages/profile.py` (including `app/pages/job_tabs/resume.py`).
  - [x] 6.4 Keep nav label as "Profile".

- [x] 7. Profile – Experience cards and dialog updates
  - [x] 7.1 In `app/pages/profile.py`, render Experience as bordered cards using `st.container(border=True)`.
  - [x] 7.2 Card header: left bold Title; right icon-only Edit/Delete buttons.
  - [x] 7.3 Subheader: `Company | Location | Mon YYYY - Mon YYYY` with `Present` if no end date.
  - [x] 7.4 Body: collapsed-by-default expander titled "Details" with description.
  - [x] 7.5 Use `confirm_delete` component for deletes; Edit triggers existing dialog.
  - [x] 7.6 In `app/dialog/experience_dialog.py`, add `Location`, set textarea height to 300, and apply `min_value=MIN_DATE` (no max).

- [x] 8. Profile – Education cards and dialog updates
  - [x] 8.1 In `app/pages/profile.py`, render Education as bordered cards with icon-only Edit/Delete.
  - [x] 8.2 Display fields: `institution`, `degree`, `major`, `grad_date` (formatted `Mon YYYY`).
  - [x] 8.3 In `app/dialog/education_dialog.py`, replace fields to match new schema and use single `Graduation Date`.
  - [x] 8.4 Apply `min_value=MIN_DATE` to date pickers and remove any `max_value`.

- [x] 9. Profile – Certificates section (new)
  - [x] 9.1 Below Education, add Certificates list as bordered cards with icon-only Edit/Delete.
  - [x] 9.2 Fields: required `title`, optional `institution`, required `date` (formatted `Mon YYYY`).
  - [x] 9.3 Add/Edit dialogs use text verbs (Save/Cancel/Delete) and `MIN_DATE`.
  - [x] 9.4 Wire to `CertificateService` for CRUD; use `confirm_delete` for deletes.

- [x] 10. Job – Resume tab add-object dialogs and integration
  - [x] 10.1 Create dialogs: `app/dialog/resume_add_experience_dialog.py`, `resume_add_education_dialog.py`, `resume_add_certificate_dialog.py` with specified layouts.
  - [x] 10.2 Implement points parsing in Experience dialog: split by newline, trim, drop empties.
  - [x] 10.3 Ensure all dialog date inputs use `min_value=MIN_DATE` with no `max_value`.
  - [x] 10.4 In `app/pages/job_tabs/resume.py`, open dialogs from "Add ..." buttons instead of inserting empty items.
  - [x] 10.5 On submit, append to `st.session_state["resume_draft"]`, set `resume_dirty=True`, and trigger preview refresh.
  - [x] 10.6 Ensure the top-info banner/button links to `pages/profile.py`.

- [x] 11. Jobs pages – Overview refactor and badges adoption
  - [x] 11.1 In `app/pages/job_tabs/overview.py`, implement header/second row layout per spec.
  - [x] 11.2 Replace any ad-hoc status UI with `render_status_badge` from `app/components/status_badge.py`.
  - [x] 11.3 Add in-place editing: Title, Company, Description; Status as dropdown; show Save/Discard while editing.
  - [x] 11.4 Extend `app/services/job_service.py.update_job_fields(...)` to persist `job_description`.
  - [x] 11.5 Rename any "Download Resume PDF" copies to "Download Resume" and remove "(disabled)" suffixes.
  - [x] 11.6 In `app/pages/jobs.py`, replace inline badge rendering with the shared Status Badge component.

- [x] 12. Shared date handling pass (incl. Onboarding)
  - [x] 12.1 Import `MIN_DATE` and remove all `max_value` from date pickers in:
    - `app/dialog/experience_dialog.py`
    - `app/dialog/education_dialog.py`
    - `app/pages/_onboarding.py`
    - `app/pages/job_tabs/resume.py`
  - [x] 12.2 In `app/pages/_onboarding.py` Step 2, add `Location` to Experience and apply min-date only.
  - [x] 12.3 In `app/pages/_onboarding.py` Step 3, collect `Institution`, `Degree`, `Major`, `Graduation Date`; apply min-date only.

- [x] 13. Logging configuration update
  - [x] 13.1 Update `src/logging_config.py` to use a single rotating file sink at `log/resume-bot.log`.
  - [x] 13.2 Configure `rotation="20 MB"` and `retention=1`; remove time from filename pattern.
  - [x] 13.3 Verify no additional historical backups are created beyond the immediate rotation.


