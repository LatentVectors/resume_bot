# Phase 1: Model & Configuration
- [x] Add `gpt-5` to `src/core/models.py` `OpenAIModels` enum as "openai:gpt-5"
- [x] Verify `get_model()` works with `gpt-5` (API key sourcing, retries)

# Phase 2: LLM Feature Module
- [x] Create `src/features/resume/llm_template.py`
- [x] Implement `generate_template_html(user_text: str, *, current_html: str | None, image: bytes | str | None) -> str`
- [x] Use `resume_template_prompt` as system; instruct model to return ONLY raw HTML
- [x] Support optional image via multimodal parts (data URL or URL)
- [x] Strip markdown fences/backticks if present; return clean HTML string

# Phase 3: Validation Helpers
- [x] Add `src/features/resume/validation.py` with minimal validator (placeholders, `{% if %}` hints)
- [x] Expose `validate_template_minimal(html_text: str) -> tuple[bool, list[str]]`

# Phase 4: Template Service (App Layer)
- [x] Create `app/services/template_service.py`
- [x] Implement `TemplateService.generate_version(user_text, image_file, current_html)` that:
  - [x] Calls `generate_template_html(...)`
  - [x] Runs `validate_template_minimal(...)` and captures warnings
  - [x] Renders HTML to PDF using `convert_html_to_pdf` with first dummy profile
  - [x] Returns `{ html, pdf_bytes, warnings }` or raises on fatal errors

# Phase 5: Streamlit Page – Templates
- [x] Create `app/pages/templates.py` (visible in sidebar titled "Templates")
- [x] Layout with `st.columns([2, 1])`
- [x] Left column (chat):
  - [x] Render chat transcript using `st.chat_message` with concise placeholders (no inline HTML)
  - [x] `st.chat_input(accept_file=True, file_type=["png","jpg","jpeg","webp"])`
  - [x] On submit: read text + optional single image, call service, append assistant placeholder (e.g., "Generated Template vN")
- [x] Right column (preview):
  - [x] Placeholder box before any render ("No template yet")
  - [x] After generation, display PDF via `st.pdf(..., height="stretch")`
  - [x] Back/forward arrows to change selected version; disable at ends
  - [x] Download controls: filename text input default `template_vN.html` + `st.download_button` (current HTML)
- [x] Show validator warnings with `st.warning`; on render failure show `st.error`

# Phase 6: Session State & Versioning
- [x] Initialize `st.session_state` keys: `tmpl_chat_messages`, `tmpl_versions`, `tmpl_selected_idx`, `tmpl_filename_input`
- [x] Store each version as `{ html: str, pdf_bytes: bytes, label: str }`
- [x] Auto-append new version after each assistant reply and select it
- [x] Label scheme: `v1`, `v2`, ... and `vN (from vX)` when editing older version

# Phase 7: Integration & Navigation
- [ ] Ensure page loads without flags and appears in sidebar
- [ ] Confirm no additional configuration is required for LangSmith

# Phase 8: QA & Testing
- [ ] Manual test: first-time generation without image
- [ ] Manual test: generation with single image attachment
- [ ] Manual test: edit latest version with feedback
- [ ] Manual test: edit from older version → label `vN (from vX)`
- [ ] Manual test: validator warnings shown but render succeeds
- [ ] Manual test: invalid HTML causes render failure error but HTML still downloadable
- [ ] Manual test: navigation arrows and download filename behavior


