from __future__ import annotations

import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from app.services.template_service import TemplateService

# ---- Session State Initialization ----
if "tmpl_chat_messages" not in st.session_state:
    st.session_state.tmpl_chat_messages = []  # list[dict]: {role, content}
if "tmpl_versions" not in st.session_state:
    st.session_state.tmpl_versions = []  # list[dict]: {html, pdf_bytes, label}
if "tmpl_selected_idx" not in st.session_state:
    st.session_state.tmpl_selected_idx = -1  # none selected
if "tmpl_filename_input" not in st.session_state:
    st.session_state.tmpl_filename_input = ""


def _current_version():
    idx = st.session_state.tmpl_selected_idx
    if 0 <= idx < len(st.session_state.tmpl_versions):
        return st.session_state.tmpl_versions[idx]
    return None


def _compute_next_label(branch_from: int | None) -> str:
    next_num = len(st.session_state.tmpl_versions) + 1
    if branch_from is None or branch_from == next_num - 1:
        return f"v{next_num}"
    return f"v{next_num} (from v{branch_from + 1})"


left_col, right_col = st.columns([1, 1])

# ---- Left: Chat Transcript and Input ----
with left_col:
    st.subheader("Template Chat")

    # Render transcript inside a fixed-height, scrollable container
    with st.container(height=460, border=True):
        for msg in st.session_state.tmpl_chat_messages:
            with st.chat_message(msg.get("role", "user")):
                st.write(msg.get("content", ""))

    # Chat input with optional single image (per spec). Some Streamlit versions may
    # return a simple string; others may return a richer object. We handle both.
    submission = st.chat_input(
        placeholder="Describe the template you want, or provide edits...",
        key="tmpl_chat_input",
        accept_file=True,
        file_type=["png", "jpg", "jpeg", "webp"],
    )

    if submission:
        text: str = ""
        image_bytes: bytes | None = None

        # Handle possible return shapes: string-only or dict-like with text/files
        if isinstance(submission, str):
            text = submission
        else:
            # Expect dict-like with keys: text, files (single file)
            try:
                text = (submission.get("text") or "").strip()
                files = submission.get("files") or []
                if files:
                    file_obj = files[0]
                    try:
                        image_bytes = file_obj.read()
                    except Exception:
                        image_bytes = None
            except Exception:
                # Fallback: best-effort to coerce to string
                text = str(submission)

        # Append user message to transcript
        st.session_state.tmpl_chat_messages.append({"role": "user", "content": text or "(no text)"})

        # Determine current_html from selected version
        selected_before = st.session_state.tmpl_selected_idx
        current_version = _current_version()
        current_html = current_version["html"] if current_version else None

        # Generate new version
        try:
            new_version = TemplateService.generate_version(
                user_text=text,
                image_file=image_bytes,
                current_html=current_html,
            )
            branch_from = selected_before if selected_before >= 0 else None
            label = _compute_next_label(branch_from)

            st.session_state.tmpl_versions.append(
                {"html": new_version.html, "pdf_bytes": new_version.pdf_bytes, "label": label}
            )
            # Select the new version
            st.session_state.tmpl_selected_idx = len(st.session_state.tmpl_versions) - 1

            # Append assistant placeholder message
            st.session_state.tmpl_chat_messages.append({"role": "assistant", "content": f"Generated Template {label}"})

            # Update default filename for download
            st.session_state.tmpl_filename_input = f"template_{label}.html"

            # Surface warnings if any
            if getattr(new_version, "warnings", None):
                for w in new_version.warnings:
                    st.warning(w)

            st.success(f"Created {label}")
            st.rerun()
        except Exception as e:  # noqa: BLE001
            st.error(f"Generation failed: {e}")

# ---- Right: Preview and Controls ----
with right_col:
    versions = st.session_state.tmpl_versions
    idx = st.session_state.tmpl_selected_idx

    # Header: Preview | back | forward | name input | download
    nav_col_preview, nav_col_back, nav_col_fwd, nav_col_name, nav_col_dl = st.columns([1, 1, 1, 4, 2])
    with nav_col_preview:
        st.text("Preview")
    with nav_col_back:
        back_disabled = idx <= 0
        if st.button("◀", disabled=back_disabled, key="tmpl_prev"):
            st.session_state.tmpl_selected_idx = max(0, idx - 1)
            sel = _current_version()
            if sel:
                st.session_state.tmpl_filename_input = f"template_{sel['label']}.html"
            st.rerun()
    with nav_col_fwd:
        fwd_disabled = idx < 0 or idx >= len(versions) - 1
        if st.button("▶", disabled=fwd_disabled, key="tmpl_next"):
            st.session_state.tmpl_selected_idx = min(len(versions) - 1, idx + 1)
            sel = _current_version()
            if sel:
                st.session_state.tmpl_filename_input = f"template_{sel['label']}.html"
            st.rerun()
    with nav_col_name:
        default_name = st.session_state.tmpl_filename_input or (
            f"template_{versions[idx]['label']}.html" if 0 <= idx < len(versions) else "template_v1.html"
        )
        filename = st.text_input(
            label="Filename",
            value=default_name,
            key="tmpl_filename_text",
            label_visibility="collapsed",
        )
        st.session_state.tmpl_filename_input = filename
    with nav_col_dl:
        sel_for_name = _current_version()
        st.download_button(
            label="Download",
            data=(sel_for_name["html"].encode("utf-8") if sel_for_name else b""),
            file_name=st.session_state.tmpl_filename_input or default_name,
            mime="text/html",
            type="primary",
            key=f"tmpl_download_{idx if idx >= 0 else 'none'}",
            disabled=(idx < 0),
        )

    if 0 <= idx < len(versions):
        sel = versions[idx]
        try:
            pdf_viewer(sel["pdf_bytes"], width="100%", height="stretch", zoom_level="auto")
        except Exception:
            st.error("Failed to render PDF preview.")
    else:
        # Placeholder box
        st.container(height=400, border=True)
        st.caption("No template yet")
