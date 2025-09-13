### Templates – Chat-based Resume Template Generation (Phase 003)

This spec defines the new "Templates" feature: a chat-driven workflow to generate and iteratively refine ATS-safe resume HTML templates, render live previews, version them, and download the resulting HTML.

## Goals
- Enable a collaborative, chat-based interface to generate/edit a resume HTML template using an LLM.
- Render the template with dummy data and display a live PDF preview.
- Maintain an in-session version history with easy navigation (back/forward) and clear labels.
- Allow downloading the currently selected template’s HTML with a user-provided filename.
- Keep the LLM service stateless; store chat and versions in the Streamlit app session only.

## Non-Goals
- Persisting chat sessions or template versions beyond the current app session.
- Building a gallery/thumbnail selection system for templates in this phase.
- Generalizing to multiple data schemas; we use the existing resume data contract.

## Page & Navigation
- **Page name**: Templates
- **Location**: Sidebar navigation (new Streamlit page file under `app/pages/`)
- **Visibility**: Visible to all users (no flags required)

## Layout & UX
- **Two columns** via `st.columns([2, 1])`.
  - Left (2/3): Chat interface
    - `st.chat_input` for user messages
    - Uses built-in file handling of `st.chat_input` (see below)
    - Chat history shows concise placeholders for assistant messages (e.g., "Generated Template v3") — do NOT display full inline HTML in the chat transcript
  - Right (1/3): Preview area
    - Shows a placeholder until first render (simple box text: "No template yet")
    - After each assistant response with valid HTML, automatically renders PDF and displays it with `st.pdf(..., height="stretch")`
    - Above preview: back/forward arrows and download controls

## Chat Input & Images
- Use `st.chat_input` with file support (per Streamlit docs):
  - `accept_file=True`
  - `file_type=["png", "jpg", "jpeg", "webp"]`
  - Only allow a single image per message
- No extra uploader component is required; rely on `st.chat_input` built-ins.
  - Return value handling: when `accept_file` is enabled, the submission provides both the entered text and uploaded files; handle the message text and, if present, a single image file object. If only text is provided, files will be empty; if only a file is provided, text may be empty.
  - Upload limits: default max upload size is controlled by Streamlit’s `server.maxUploadSize` (MB). We won’t change this in this phase; large files will be rejected by Streamlit automatically.

## LLM Model & Prompting
- **System prompt**: Use `src/features/resume/prompt.py` (`resume_template_prompt`) verbatim.
- **Model**: Prefer `gpt-5`.
  - Add to `src/core/models.py` enum as `openai:gpt-5` (e.g., `OpenAIModels.gpt_5`)
  - Use existing `get_model` factory
- **Instruction to model**: Always instruct to return ONLY raw HTML with no prose, markdown, or code fences.
- **Message strategy**:
  - First generation: pass latest user message and optional image. The assistant responds with complete HTML template.
  - Edit loop: pass the user’s latest feedback and the currently selected template’s full HTML; request a modified full HTML template.
  - Only the latest user message and the currently selected template are included (no full running history in the prompt) to keep the call simple and stateless.
- **Multimodal**: If an image is attached, include it in the user message content per LangChain multimodal message format.
- **Tracing**: LangSmith is already configured; no additional work required.

## Rendering & Dummy Data
- Use existing `src/features/resume/utils.py` rendering pipeline with WeasyPrint.
  - Prefer `convert_html_to_pdf(html_content, output_path)` for PDF generation.
- Dummy data: use the first entry in `DUMMY_RESUME_DATA` from `src/features/resume/content.py`.
- Rendering happens automatically on every successful LLM response producing HTML.
  - The rendered PDF is appended as a new version in the carousel and becomes the currently selected version.

## Versioning (Carousel)
- Maintain an in-session list of versions. Each version stores:
  - `html`: the full template HTML
  - `pdf_bytes`: the rendered PDF bytes
  - `label`: e.g., `v1`, `v2`, … or `vN (from vX)` when editing from an older version
- Back and forward arrows cycle the currently selected index; buttons are disabled at ends.
- Selecting an older version does NOT call the LLM; it only switches what is shown. If the user submits edits while an older version is selected, generate a new version labeled `vN+1 (from vX)`.
- Do not display timestamps in the UI.

## Downloading HTML
- Replace "Copy" with a download flow:
  - Provide a filename text input, defaulting to `template_vN.html` for the selected version.
  - `st.download_button` to download the HTML of the currently selected version.
  - Optionally normalize/truncate whitespace and strip unintended markdown fences if present.

## Validation & Error Handling
- Use a minimal validator similar to `src/features/resume/cli.py::_validate_template_minimal`:
  - Warn for missing placeholders or missing `{% if %}` wrappers; still attempt rendering.
  - If rendering fails, show an error in the preview pane and keep the HTML available for download.
- When the model returns non-HTML content:
  - Attempt to extract/clean HTML (e.g., remove ``` blocks) and validate again; if still invalid, show an error and retain raw content for user review/download.

## State Management
- Store state in `st.session_state`:
  - `tmpl_chat_messages`: list of `{ role: "user"|"assistant", content: str, has_image: bool }`
  - `tmpl_versions`: list of `{ html: str, pdf_bytes: bytes, label: str }`
  - `tmpl_selected_idx`: int index of the currently visible version
  - `tmpl_filename_input`: str for the download filename input
- This is sufficient for this phase (low expected usage). Recommendation: if usage grows, consider either: (1) bounding history to a max (e.g., 25 versions) or (2) offloading PDFs to a temp directory and caching only paths.

## Services & Module Boundaries
- Create `app/services/template_service.py` to coordinate chat interactions from the Streamlit page.
  - Responsibilities: receive user text + optional image handle, get current HTML (if any), call the feature LLM function, validate, render, and return the new version.
- Create `src/features/resume/llm_template.py` (new) exposing a single function:
  - `generate_template_html(user_text: str, *, current_html: str | None, image: bytes | str | None) -> str`
    - Formats LangChain messages using `resume_template_prompt` as system.
    - If `image` is provided, include as `image_url` or data URL content part.
    - Uses `get_model(OpenAIModels.gpt_5)` and returns raw HTML string only.

## Streamlit Page Structure (High-Level)
1) Initialize session keys if missing
2) Layout with `st.columns([2, 1])`
3) Left column: chat history and `st.chat_input(accept_file=True, file_type=[...])`
4) On submit:
   - Read user text and optional image from `st.chat_input` result
   - Determine `current_html` from selected version (if any)
   - Call `TemplateService.send_message(...)`
   - Append assistant placeholder message (e.g., "Generated Template vN") to chat history
   - Update versions list, set `tmpl_selected_idx` to the new version
5) Right column: preview header (back/forward + download filename + download button)
6) Render `st.pdf` with selected version’s `pdf_bytes`, or show placeholder if none

## Configuration & Model Enum Update
- Update `src/core/models.py`:
  - Add enum member `gpt_5 = "openai:gpt-5"`
  - No other configuration changes; `get_model` already handles OpenAI API key.

## Acceptance Criteria
- Templates page appears in the sidebar titled "Templates".
- Left 2/3 chat, right 1/3 preview; placeholder shown before first render; preview uses `st.pdf(..., height="stretch")`.
- `st.chat_input` supports exactly one image per message via `accept_file=True` and restricted image types.
- First prompt and subsequent edits follow the system prompt from `resume/prompt.py` verbatim.
- Model used is `gpt-5`; output is strictly raw HTML (no markdown, no prose).
- After each assistant response, the HTML is validated, rendered with dummy data (first profile), added as a new version, auto-selected, and displayed.
- Version navigation via back/forward arrows works; labels are `v1`, `v2`, … with `(from vX)` when branching from older versions.
- Download button lets user set filename and download the current version’s HTML.
- Invalid templates show warnings; failed renders show an error while preserving HTML for download.
- All state is kept in `st.session_state`; nothing is persisted to disk (beyond ephemeral rendering needs).

## Implementation Tasks
- Page: `app/pages/templates.py` with described layout and behavior
- Service: `app/services/template_service.py` to orchestrate LLM calls, validation, and rendering
- Feature function: `src/features/resume/llm_template.py` with `generate_template_html(...)`
- Enum: add `gpt-5` to `src/core/models.py`
- Small validator reuse or helper in `src/features/resume` for warnings

## Future Enhancements (Out of Scope for This Phase)
- Persist chat sessions and versions with thumbnails of rendered templates
- Template gallery and template selection for resume generation
- More advanced validation and contract enforcement
- Performance optimizations for large/complex templates and many versions

## Streamlit Chat Components – Doc Clarifications
- `st.chat_input`:
  - Supports file attachments via `accept_file` and restricts extensions via `file_type`.
  - For single-file behavior, use `accept_file=True` (do not use the multiple-files mode).
  - On submit, handle both the textual message and any uploaded file(s). Expect none/one file in this feature.
  - Standard parameters like `placeholder`, `key`, and `disabled` are available; we’ll use a `placeholder` and a dedicated `key` for stability across reruns.
- `st.chat_message`:
  - Use to render the transcript, one container per message, with roles like `"user"` and `"assistant"`.
  - We will not render full HTML inside messages; instead, show concise placeholders (e.g., version labels) to keep the transcript readable.


