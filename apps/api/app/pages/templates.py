from __future__ import annotations

import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from app.services.cover_letter_template_service import CoverLetterTemplateService
from app.services.template_service import TemplateService

# ---- Tab Selection ----
if "selected_template_tab" not in st.session_state:
    st.session_state.selected_template_tab = "Resume"

selected_tab = st.segmented_control(
    label="Template Type",
    options=["Resume", "Cover Letter"],
    default=st.session_state.selected_template_tab,
    key="template_tab_control",
    label_visibility="collapsed",
)
# Only update if it actually changed
if selected_tab != st.session_state.selected_template_tab:
    st.session_state.selected_template_tab = selected_tab
    st.rerun()

# ---- Session State Initialization: Resume ----
if "resume_tmpl_chat_messages" not in st.session_state:
    st.session_state.resume_tmpl_chat_messages = []  # list[dict]: {role, content}
if "resume_tmpl_versions" not in st.session_state:
    st.session_state.resume_tmpl_versions = []  # list[dict]: {html, pdf_bytes, label}
if "resume_tmpl_selected_idx" not in st.session_state:
    st.session_state.resume_tmpl_selected_idx = -1  # none selected

# ---- Session State Initialization: Cover Letter ----
if "cover_tmpl_chat_messages" not in st.session_state:
    st.session_state.cover_tmpl_chat_messages = []  # list[dict]: {role, content}
if "cover_tmpl_versions" not in st.session_state:
    st.session_state.cover_tmpl_versions = []  # list[dict]: {html, pdf_bytes, label}
if "cover_tmpl_selected_idx" not in st.session_state:
    st.session_state.cover_tmpl_selected_idx = -1  # none selected


def _current_version(session_key_prefix: str):
    """Get currently selected version for the given prefix (resume_tmpl or cover_tmpl)."""
    idx = st.session_state[f"{session_key_prefix}_selected_idx"]
    versions = st.session_state[f"{session_key_prefix}_versions"]
    if 0 <= idx < len(versions):
        return versions[idx]
    return None


def _compute_next_label(session_key_prefix: str, branch_from: int | None) -> str:
    """Compute label for next version."""
    versions = st.session_state[f"{session_key_prefix}_versions"]
    next_num = len(versions) + 1
    if branch_from is None or branch_from == next_num - 1:
        return f"v{next_num}"
    return f"v{next_num} (from v{branch_from + 1})"


# ==================== RESUME TAB ====================
if selected_tab == "Resume":
    left_col, right_col = st.columns([1, 1])

    # ---- Left: Chat Transcript and Input ----
    with left_col:
        st.subheader("Resume Template Chat")

        # Render transcript inside a fixed-height, scrollable container
        with st.container(height=460, border=True):
            for msg in st.session_state.resume_tmpl_chat_messages:
                with st.chat_message(msg.get("role", "user")):
                    st.write(msg.get("content", ""))

        # Chat input with optional single image (per spec). Some Streamlit versions may
        # return a simple string; others may return a richer object. We handle both.
        submission = st.chat_input(
            placeholder="Describe the template you want, or provide edits...",
            key="resume_tmpl_chat_input",
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
            st.session_state.resume_tmpl_chat_messages.append({"role": "user", "content": text or "(no text)"})

            # Determine current_html from selected version
            selected_before = st.session_state.resume_tmpl_selected_idx
            current_version = _current_version("resume_tmpl")
            current_html = current_version["html"] if current_version else None

            # Generate new version
            try:
                new_version = TemplateService.generate_version(
                    user_text=text,
                    image_file=image_bytes,
                    current_html=current_html,
                )
                branch_from = selected_before if selected_before >= 0 else None
                label = _compute_next_label("resume_tmpl", branch_from)

                st.session_state.resume_tmpl_versions.append(
                    {"html": new_version.html, "pdf_bytes": new_version.pdf_bytes, "label": label}
                )
                # Select the new version
                st.session_state.resume_tmpl_selected_idx = len(st.session_state.resume_tmpl_versions) - 1

                # Append assistant placeholder message
                st.session_state.resume_tmpl_chat_messages.append(
                    {"role": "assistant", "content": f"Generated Template {label}"}
                )

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
        versions = st.session_state.resume_tmpl_versions
        idx = st.session_state.resume_tmpl_selected_idx

        # Header: navigation controls (left), version label (center), and action buttons (right)
        nav_left, nav_center, nav_right = st.columns([1, 1, 2])

        with nav_left:
            with st.container(horizontal=True, horizontal_alignment="left"):
                back_disabled = idx <= 0
                if st.button("◀", disabled=back_disabled, key="resume_tmpl_prev", help="Previous version"):
                    st.session_state.resume_tmpl_selected_idx = max(0, idx - 1)
                    st.rerun()

                fwd_disabled = idx < 0 or idx >= len(versions) - 1
                if st.button("▶", disabled=fwd_disabled, key="resume_tmpl_next", help="Next version"):
                    st.session_state.resume_tmpl_selected_idx = min(len(versions) - 1, idx + 1)
                    st.rerun()

        with nav_center:
            sel = _current_version("resume_tmpl")
            if sel:
                st.markdown(f"**{sel['label']}**")

        with nav_right:
            with st.container(horizontal=True, horizontal_alignment="right"):
                sel = _current_version("resume_tmpl")

                # Copy button
                copy_clicked = st.button(
                    ":material/content_copy:",
                    help="Copy HTML to clipboard",
                    key="resume_tmpl_copy",
                    disabled=(idx < 0),
                )
                if copy_clicked and sel:
                    try:
                        import importlib

                        pyperclip = importlib.import_module("pyperclip")
                        pyperclip.copy(sel["html"])
                        st.toast("Copied HTML to clipboard!")
                    except Exception as e:
                        st.error(f"Failed to copy: {e}")

                # Download button with auto-generated filename
                download_filename = f"template_{sel['label']}.html" if sel else "template_v1.html"
                st.download_button(
                    label="Download",
                    data=(sel["html"].encode("utf-8") if sel else b""),
                    file_name=download_filename,
                    mime="text/html",
                    type="primary",
                    key=f"resume_tmpl_download_{idx if idx >= 0 else 'none'}",
                    disabled=(idx < 0),
                )

        if 0 <= idx < len(versions):
            sel = versions[idx]
            try:
                # Use fixed height in pixels instead of "stretch" for better compatibility
                pdf_viewer(sel["pdf_bytes"], width=700, height=900)
            except Exception as e:
                st.error(f"Failed to render PDF preview: {e}")
                # Show HTML as fallback for debugging
                with st.expander("View HTML (Debug)"):
                    st.code(sel["html"], language="html")
        else:
            # Placeholder box
            st.container(height=400, border=True)
            st.caption("No template yet")


# ==================== COVER LETTER TAB ====================
elif selected_tab == "Cover Letter":
    left_col, right_col = st.columns([1, 1])

    # ---- Left: Chat Transcript and Input ----
    with left_col:
        st.subheader("Cover Letter Template Chat")

        # Render transcript inside a fixed-height, scrollable container
        with st.container(height=460, border=True):
            for msg in st.session_state.cover_tmpl_chat_messages:
                with st.chat_message(msg.get("role", "user")):
                    st.write(msg.get("content", ""))

        # Chat input with optional single image (per spec). Some Streamlit versions may
        # return a simple string; others may return a richer object. We handle both.
        submission = st.chat_input(
            placeholder="Describe the template you want, or provide edits...",
            key="cover_tmpl_chat_input",
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
            st.session_state.cover_tmpl_chat_messages.append({"role": "user", "content": text or "(no text)"})

            # Determine current_html from selected version
            selected_before = st.session_state.cover_tmpl_selected_idx
            current_version = _current_version("cover_tmpl")
            current_html = current_version["html"] if current_version else None

            # Generate new version
            try:
                new_version = CoverLetterTemplateService.generate_version(
                    user_text=text,
                    image_file=image_bytes,
                    current_html=current_html,
                )
                branch_from = selected_before if selected_before >= 0 else None
                label = _compute_next_label("cover_tmpl", branch_from)

                st.session_state.cover_tmpl_versions.append(
                    {"html": new_version.html, "pdf_bytes": new_version.pdf_bytes, "label": label}
                )
                # Select the new version
                st.session_state.cover_tmpl_selected_idx = len(st.session_state.cover_tmpl_versions) - 1

                # Append assistant placeholder message
                st.session_state.cover_tmpl_chat_messages.append(
                    {"role": "assistant", "content": f"Generated Template {label}"}
                )

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
        versions = st.session_state.cover_tmpl_versions
        idx = st.session_state.cover_tmpl_selected_idx

        # Header: navigation controls (left), version label (center), and action buttons (right)
        nav_left, nav_center, nav_right = st.columns([1, 1, 2])

        with nav_left:
            with st.container(horizontal=True, horizontal_alignment="left"):
                back_disabled = idx <= 0
                if st.button("◀", disabled=back_disabled, key="cover_tmpl_prev", help="Previous version"):
                    st.session_state.cover_tmpl_selected_idx = max(0, idx - 1)
                    st.rerun()

                fwd_disabled = idx < 0 or idx >= len(versions) - 1
                if st.button("▶", disabled=fwd_disabled, key="cover_tmpl_next", help="Next version"):
                    st.session_state.cover_tmpl_selected_idx = min(len(versions) - 1, idx + 1)
                    st.rerun()

        with nav_center:
            sel = _current_version("cover_tmpl")
            if sel:
                st.markdown(f"**{sel['label']}**")

        with nav_right:
            with st.container(horizontal=True, horizontal_alignment="right"):
                sel = _current_version("cover_tmpl")

                # Copy button
                copy_clicked = st.button(
                    ":material/content_copy:",
                    help="Copy HTML to clipboard",
                    key="cover_tmpl_copy",
                    disabled=(idx < 0),
                )
                if copy_clicked and sel:
                    try:
                        import importlib

                        pyperclip = importlib.import_module("pyperclip")
                        pyperclip.copy(sel["html"])
                        st.toast("Copied HTML to clipboard!")
                    except Exception as e:
                        st.error(f"Failed to copy: {e}")

                # Download button with auto-generated filename
                download_filename = (
                    f"cover_letter_template_{sel['label']}.html" if sel else "cover_letter_template_v1.html"
                )
                st.download_button(
                    label="Download",
                    data=(sel["html"].encode("utf-8") if sel else b""),
                    file_name=download_filename,
                    mime="text/html",
                    type="primary",
                    key=f"cover_tmpl_download_{idx if idx >= 0 else 'none'}",
                    disabled=(idx < 0),
                )

        if 0 <= idx < len(versions):
            sel = versions[idx]
            try:
                # Use fixed height in pixels instead of "stretch" for better compatibility
                pdf_viewer(sel["pdf_bytes"])
            except Exception as e:
                st.error(f"Failed to render PDF preview: {e}")
                # Show HTML as fallback for debugging
                with st.expander("View HTML (Debug)"):
                    st.code(sel["html"], language="html")
        else:
            # Placeholder box
            st.container(height=400, border=True)
            st.caption("No template yet")
