"""Step 2: Experience & Resume Development with chat and editing."""

from __future__ import annotations

import re
from typing import cast

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from streamlit_pdf_viewer import pdf_viewer

from app.constants import MIN_DATE
from app.dialog.resume_add_certificate_dialog import show_resume_add_certificate_dialog
from app.dialog.resume_add_education_dialog import show_resume_add_education_dialog
from app.dialog.resume_add_experience_dialog import show_resume_add_experience_dialog
from app.pages.job_tabs.utils import navigate_to_job
from app.services.job_intake_service import JobIntakeService
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from app.services.user_service import UserService
from app.shared.filenames import build_resume_download_filename
from src.features.resume.types import (
    ResumeCertification,
    ResumeData,
    ResumeEducation,
    ResumeExperience,
)
from src.logging_config import logger


def render_step2_experience_and_resume(job_id: int | None) -> None:
    """Render Step 2: Experience & Resume Development.

    Args:
        job_id: The job ID for this intake session.
    """
    if not job_id:
        st.error("No job ID provided. Cannot proceed with experience & resume development.")
        return

    # Progress indicator
    st.caption("Step 2 of 2: Experience & Resume Development")
    st.markdown("---")

    # Get job and session
    job = JobService.get_job(job_id)
    if not job:
        st.error("Job not found.")
        return

    session = JobService.get_intake_session(job_id)
    if not session:
        st.error("Intake session not found.")
        return

    # Validate that analyses are available
    if not session.gap_analysis or not session.gap_analysis.strip():
        st.error("Unable to load analyses. Please restart intake flow.")
        logger.error("Gap analysis missing for job_id=%s", job_id)
        return

    if not session.stakeholder_analysis or not session.stakeholder_analysis.strip():
        st.error("Unable to load analyses. Please restart intake flow.")
        logger.error("Stakeholder analysis missing for job_id=%s", job_id)
        return

    user = UserService.get_current_user()
    if not user or not user.id:
        st.error("User not found.")
        return

    # Get all versions
    versions = ResumeService.list_versions(job_id)
    if not versions:
        st.warning("No resume versions found. You may skip this step.")
        with st.container(horizontal=True, horizontal_alignment="right"):
            if st.button("Skip", key="step2_skip_no_versions"):
                try:
                    JobIntakeService.complete_step2_final(session.id, job_id, pin_version_id=None)
                    _clear_step2_state(job_id)
                    navigate_to_job(job_id)
                except Exception as exc:
                    logger.exception("Error completing step 2 (skip): %s", exc)
                    st.error("Failed to complete step. Please try again.")
                st.rerun()
        return

    # Get selected version
    selected_version_id = st.session_state.get("step2_selected_version_id")
    selected_version = None
    if selected_version_id:
        for v in versions:
            if v.id == selected_version_id:
                selected_version = v
                break

    # Default to latest if not found
    if not selected_version:
        selected_version = versions[-1]
        st.session_state.step2_selected_version_id = selected_version.id

    # Load draft from selected version if not in session or version changed
    if "step2_draft" not in st.session_state or st.session_state.get("step2_loaded_version_id") != selected_version.id:
        try:
            draft = ResumeData.model_validate_json(selected_version.resume_json)
            st.session_state.step2_draft = draft
            st.session_state.step2_loaded_version_id = selected_version.id
            st.session_state.step2_dirty = False
        except Exception as exc:
            logger.exception("Failed to load resume data: %s", exc)
            st.error("Failed to load resume data")
            return

    # Two-column layout [4, 3]
    left_col, right_col = st.columns([4, 3])

    # LEFT COLUMN: Chat interface
    with left_col:
        _render_step2_chat(job, versions, selected_version)

    # RIGHT COLUMN: Analysis and Resume tabs
    with right_col:
        # Create 4 tabs for analyses and resume
        tab1, tab2, tab3, tab4 = st.tabs(["Gap Analysis", "Stakeholder Analysis", "Resume Content", "Resume PDF"])

        with tab1:
            # Display gap analysis as markdown
            st.markdown(session.gap_analysis)

        with tab2:
            # Display stakeholder analysis as markdown
            st.markdown(session.stakeholder_analysis)

        with tab3:
            # Display resume content editor
            _render_step2_resume_content_tab(job_id, versions, selected_version)

        with tab4:
            # Display resume PDF preview
            _render_step2_resume_pdf_tab(job_id, versions, selected_version)

    # Action buttons
    st.markdown("---")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Skip", key="intake_step2_skip"):
            try:
                JobIntakeService.complete_step2_final(session.id, job_id, pin_version_id=None)
                _clear_step2_state(job_id)
                navigate_to_job(job_id)
            except Exception as exc:
                logger.exception("Error completing step 2 (skip): %s", exc)
                st.error("Failed to complete step. Please try again.")
            st.rerun()

        # Next enabled when version selected
        next_enabled = selected_version_id is not None
        if st.button("Next", type="primary", disabled=not next_enabled, key="intake_step2_next"):
            try:
                JobIntakeService.complete_step2_final(session.id, job_id, pin_version_id=selected_version_id)
                _clear_step2_state(job_id)
                navigate_to_job(job_id)
            except Exception as exc:
                logger.exception("Error completing step 2 (with pin): %s", exc)
                st.error("Failed to complete step. Please try again.")
            st.rerun()


# ==================== Chat Section ====================


def _render_step2_chat(job, versions: list, selected_version) -> None:
    """Render chat interface for Step 2 experience & resume development.

    Args:
        job: Job object
        versions: List of resume versions
        selected_version: Currently selected version
    """
    # Initialize chat messages if needed
    if "step2_messages" not in st.session_state:
        st.session_state.step2_messages = []

    # Fixed-height container for chat history (500px)
    with st.container(height=500):
        # Display chat messages
        for msg in st.session_state.step2_messages:
            if isinstance(msg, HumanMessage):
                with st.chat_message("user"):
                    st.markdown(msg.content)
            elif isinstance(msg, AIMessage):
                with st.chat_message("assistant"):
                    st.markdown(msg.content)
            elif isinstance(msg, ToolMessage):
                with st.chat_message("assistant"):
                    st.caption("🔧 Resume draft created")
                    st.text(msg.content)

    # Chat input below the fixed container
    if user_input := st.chat_input("Ask for resume changes..."):
        # Add user message
        st.session_state.step2_messages.append(HumanMessage(content=user_input))

        # Get AI response with tool
        with st.spinner("Thinking..."):
            ai_response, new_version_id = JobIntakeService.get_resume_chat_response(
                st.session_state.step2_messages,
                job,
                selected_version,
            )
            st.session_state.step2_messages.append(ai_response)

            # Execute tools immediately when AI calls them
            if hasattr(ai_response, "tool_calls") and ai_response.tool_calls:
                for tool_call in ai_response.tool_calls:
                    # Execute the actual tool function to get its return value
                    tool_result = _invoke_resume_tool(tool_call)

                    # Add ToolMessage with actual tool result
                    tool_msg = ToolMessage(content=tool_result, tool_call_id=tool_call.get("id"))
                    st.session_state.step2_messages.append(tool_msg)

            # If AI created a new version, update selection
            if new_version_id:
                st.session_state.step2_selected_version_id = new_version_id

        st.rerun()


# ==================== Resume Preview/Edit Section ====================


def _render_step2_resume_preview(job_id: int, versions: list, selected_version) -> None:
    """Render resume preview/edit section for Step 2.

    Args:
        job_id: Job ID
        versions: List of resume versions
        selected_version: Currently selected version
    """
    # Get canonical version ID for pin indicator
    try:
        canonical_row = ResumeService.get_canonical(job_id)
    except Exception as exc:
        logger.exception("Failed to get canonical: %s", exc)
        canonical_row = None

    canonical_version_id = None
    if canonical_row and versions:
        for v in reversed(versions):
            try:
                if v.template_name == canonical_row.template_name and v.resume_json == canonical_row.resume_json:
                    canonical_version_id = cast(int, v.id)
                    break
            except Exception:
                continue

    # Row 1: Version navigation (< | dropdown | > | pin)
    with st.container(horizontal=True, horizontal_alignment="right"):
        current_index = int(selected_version.version_index)
        min_index = 1
        max_index = int(versions[-1].version_index)

        # Left arrow
        go_left = st.button(
            ":material/chevron_left:",
            key="step2_ver_left",
            disabled=current_index <= min_index,
            help="Older version",
        )

        # Dropdown of versions in descending order (vN..v1) with pin indicator
        try:
            versions_desc = sorted(versions, key=lambda v: int(v.version_index), reverse=True)
        except Exception:
            versions_desc = list(reversed(versions))

        labels = []
        for v in versions_desc:
            label = f"v{v.version_index}"
            if canonical_version_id and cast(int, v.id) == canonical_version_id:
                label += " (pinned)"
            labels.append(label)

        indices = [int(v.version_index) for v in versions_desc]
        try:
            dd_idx = indices.index(current_index)
        except ValueError:
            dd_idx = 0  # default to newest (first)

        chosen_label = st.selectbox(
            "Version",
            options=labels,
            index=dd_idx,
            label_visibility="collapsed",
            key="step2_version_select",
        )

        # Right arrow
        go_right = st.button(
            ":material/chevron_right:",
            key="step2_ver_right",
            disabled=current_index >= max_index,
            help="Newer version",
        )

        # Pin icon
        selected_is_canonical = (
            selected_version.id is not None
            and canonical_version_id is not None
            and selected_version.id == canonical_version_id
        )
        pin_label = ":material/keep:" if selected_is_canonical else ":material/keep_off:"
        pin_help = "Pinned (canonical)" if selected_is_canonical else "Set selected version as canonical"
        pin_type = "primary" if selected_is_canonical else "secondary"
        pin_clicked = st.button(pin_label, help=pin_help, key="step2_pin_btn", type=pin_type)

    # Handle version navigation
    new_selected_id = None
    if go_left:
        target_index = current_index - 1
        for v in versions:
            if int(v.version_index) == target_index:
                new_selected_id = cast(int, v.id)
                break
    elif go_right:
        target_index = current_index + 1
        for v in versions:
            if int(v.version_index) == target_index:
                new_selected_id = cast(int, v.id)
                break
    else:
        # Dropdown change
        try:
            chosen_index = int(chosen_label.replace(" (pinned)", "").removeprefix("v"))
            if chosen_index != current_index:
                for v in versions:
                    if int(v.version_index) == chosen_index:
                        new_selected_id = cast(int, v.id)
                        break
        except Exception:
            pass

    if pin_clicked and selected_version.id is not None:
        try:
            ResumeService.pin_canonical(job_id, selected_version.id)
            st.toast("Pinned canonical resume.")
        except Exception as exc:
            logger.exception("Failed to pin canonical: %s", exc)
            st.error("Failed to set canonical resume.")
        st.rerun()

    if new_selected_id is not None:
        st.session_state.step2_selected_version_id = new_selected_id
        # Load new version into draft
        for v in versions:
            if v.id == new_selected_id:
                try:
                    new_draft = ResumeData.model_validate_json(v.resume_json)
                    st.session_state.step2_draft = new_draft
                    st.session_state.step2_loaded_version_id = new_selected_id
                    st.session_state.step2_dirty = False
                except Exception as exc:
                    logger.exception("Failed to load version: %s", exc)
                break
        st.rerun()

    # Row 2: View mode selector (left) | Action buttons (right)
    resume_data = st.session_state.get("step2_draft")
    if not resume_data:
        try:
            resume_data = ResumeData.model_validate_json(selected_version.resume_json)
        except Exception as exc:
            logger.exception("Failed to parse resume data: %s", exc)
            st.error("Failed to load resume data")
            return

    # Check if dirty
    is_dirty = st.session_state.get("step2_dirty", False)

    # Check if selected version is canonical (pinned)
    selected_is_canonical = (
        selected_version.id is not None
        and canonical_version_id is not None
        and selected_version.id == canonical_version_id
    )

    row2_col1, row2_col2 = st.columns([1, 2])

    with row2_col1:
        # Segmented control for PDF/Edit (left-aligned)
        # Ensure view mode is always set, preserve when switching versions
        if "step2_view_mode" not in st.session_state:
            st.session_state.step2_view_mode = "PDF"

        current_view_mode = st.session_state.step2_view_mode
        view_mode = st.segmented_control(
            "View",
            options=["PDF", "Edit"],
            selection_mode="single",
            default=current_view_mode,
            label_visibility="collapsed",
            key="step2_view_mode_control",
        )

        # Update session state - ensure it's never None
        st.session_state.step2_view_mode = view_mode if view_mode else current_view_mode

    with row2_col2:
        # Right-aligned buttons: Copy/Download OR Discard/Save based on dirty state
        with st.container(horizontal=True, horizontal_alignment="right"):
            if is_dirty:
                # Show Discard and Save when there are unsaved changes
                if st.button("Discard", key="step2_discard_changes"):
                    # Reload from selected version
                    try:
                        original_draft = ResumeData.model_validate_json(selected_version.resume_json)
                        st.session_state.step2_draft = original_draft
                        st.session_state.step2_dirty = False
                        st.rerun()
                    except Exception as exc:
                        logger.exception("Failed to discard changes: %s", exc)
                        st.error("Failed to discard changes")

                if st.button("Save", type="primary", key="step2_save_changes"):
                    try:
                        new_version_id = JobIntakeService.save_manual_resume_edit(job_id, selected_version, resume_data)
                        # Update selection
                        st.session_state.step2_selected_version_id = new_version_id
                        st.session_state.step2_draft = resume_data
                        st.session_state.step2_loaded_version_id = new_version_id
                        st.session_state.step2_dirty = False
                        st.toast("Changes saved as new version!")
                        st.rerun()
                    except Exception as exc:
                        logger.exception("Failed to save changes: %s", exc)
                        st.error("Failed to save changes")
            else:
                # Show Copy and Download when no unsaved changes
                # Copy button (icon only)
                if st.button(":material/content_copy:", key="step2_copy", help="Copy resume text"):
                    try:
                        import pyperclip

                        pyperclip.copy(str(resume_data))
                        st.toast("Copied to clipboard!")
                    except Exception as exc:
                        logger.exception("Failed to copy: %s", exc)
                        st.error("Failed to copy to clipboard")

                # Download button (text only, enabled only when pinned, primary button)
                download_help = None if selected_is_canonical else "Pin this version to enable download"
                try:
                    pdf_bytes = ResumeService.render_preview(job_id, resume_data, selected_version.template_name)
                    job = JobService.get_job(job_id)
                    filename = build_resume_download_filename(job.company_name, job.job_title, resume_data.name)

                    st.download_button(
                        label="Download",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        disabled=not selected_is_canonical,
                        type="primary",
                        help=download_help,
                        key="step2_download",
                    )
                except Exception as exc:
                    logger.exception("Failed to render PDF: %s", exc)
                    st.button("Download", disabled=True, type="primary", key="step2_download_disabled")

    # Show preview or edit based on view mode
    current_view_mode = st.session_state.get("step2_view_mode", "PDF")

    if current_view_mode == "PDF":
        # PDF preview
        try:
            pdf_bytes = ResumeService.render_preview(job_id, resume_data, selected_version.template_name)
            pdf_viewer(pdf_bytes, zoom_level="auto")
        except Exception as exc:
            logger.exception("Failed to render PDF: %s", exc)
            st.error("Failed to render PDF preview")
    else:
        # Edit mode with expandable sections (identical to resume tab)
        _render_edit_mode(job_id, selected_version)


def _render_step2_resume_content_tab(job_id: int, versions: list, selected_version) -> None:
    """Render resume content editing tab for Step 2.

    Args:
        job_id: Job ID
        versions: List of resume versions
        selected_version: Currently selected version
    """
    _render_version_navigation_and_content(job_id, versions, selected_version, show_pdf=False)


def _render_step2_resume_pdf_tab(job_id: int, versions: list, selected_version) -> None:
    """Render resume PDF preview tab for Step 2.

    Args:
        job_id: Job ID
        versions: List of resume versions
        selected_version: Currently selected version
    """
    _render_version_navigation_and_content(job_id, versions, selected_version, show_pdf=True)


def _render_version_navigation_and_content(job_id: int, versions: list, selected_version, show_pdf: bool) -> None:
    """Render version navigation controls and content (PDF or edit form).

    Args:
        job_id: Job ID
        versions: List of resume versions
        selected_version: Currently selected version
        show_pdf: If True, show PDF preview; if False, show edit form
    """
    # Get canonical version ID for pin indicator
    try:
        canonical_row = ResumeService.get_canonical(job_id)
    except Exception as exc:
        logger.exception("Failed to get canonical: %s", exc)
        canonical_row = None

    canonical_version_id = None
    if canonical_row and versions:
        for v in reversed(versions):
            try:
                if v.template_name == canonical_row.template_name and v.resume_json == canonical_row.resume_json:
                    canonical_version_id = cast(int, v.id)
                    break
            except Exception:
                continue

    # Row 1: Version navigation (< | dropdown | > | pin)
    # Use different keys for content vs PDF tab to avoid conflicts
    tab_suffix = "pdf" if show_pdf else "content"

    with st.container(horizontal=True, horizontal_alignment="right"):
        current_index = int(selected_version.version_index)
        min_index = 1
        max_index = int(versions[-1].version_index)

        # Left arrow
        go_left = st.button(
            ":material/chevron_left:",
            key=f"step2_ver_left_{tab_suffix}",
            disabled=current_index <= min_index,
            help="Older version",
        )

        # Dropdown of versions in descending order (vN..v1) with pin indicator
        try:
            versions_desc = sorted(versions, key=lambda v: int(v.version_index), reverse=True)
        except Exception:
            versions_desc = list(reversed(versions))

        labels = []
        for v in versions_desc:
            label = f"v{v.version_index}"
            if canonical_version_id and cast(int, v.id) == canonical_version_id:
                label += " (pinned)"
            labels.append(label)

        indices = [int(v.version_index) for v in versions_desc]
        try:
            dd_idx = indices.index(current_index)
        except ValueError:
            dd_idx = 0  # default to newest (first)

        chosen_label = st.selectbox(
            "Version",
            options=labels,
            index=dd_idx,
            label_visibility="collapsed",
            key=f"step2_version_select_{tab_suffix}",
        )

        # Right arrow
        go_right = st.button(
            ":material/chevron_right:",
            key=f"step2_ver_right_{tab_suffix}",
            disabled=current_index >= max_index,
            help="Newer version",
        )

        # Pin icon
        selected_is_canonical = (
            selected_version.id is not None
            and canonical_version_id is not None
            and selected_version.id == canonical_version_id
        )
        pin_label = ":material/keep:" if selected_is_canonical else ":material/keep_off:"
        pin_help = "Pinned (canonical)" if selected_is_canonical else "Set selected version as canonical"
        pin_type = "primary" if selected_is_canonical else "secondary"
        pin_clicked = st.button(pin_label, help=pin_help, key=f"step2_pin_btn_{tab_suffix}", type=pin_type)

    # Handle version navigation
    new_selected_id = None
    if go_left:
        target_index = current_index - 1
        for v in versions:
            if int(v.version_index) == target_index:
                new_selected_id = cast(int, v.id)
                break
    elif go_right:
        target_index = current_index + 1
        for v in versions:
            if int(v.version_index) == target_index:
                new_selected_id = cast(int, v.id)
                break
    else:
        # Dropdown change
        try:
            chosen_index = int(chosen_label.replace(" (pinned)", "").removeprefix("v"))
            if chosen_index != current_index:
                for v in versions:
                    if int(v.version_index) == chosen_index:
                        new_selected_id = cast(int, v.id)
                        break
        except Exception:
            pass

    if pin_clicked and selected_version.id is not None:
        try:
            ResumeService.pin_canonical(job_id, selected_version.id)
            st.toast("Pinned canonical resume.")
        except Exception as exc:
            logger.exception("Failed to pin canonical: %s", exc)
            st.error("Failed to set canonical resume.")
        st.rerun()

    if new_selected_id is not None:
        st.session_state.step2_selected_version_id = new_selected_id
        # Load new version into draft
        for v in versions:
            if v.id == new_selected_id:
                try:
                    new_draft = ResumeData.model_validate_json(v.resume_json)
                    st.session_state.step2_draft = new_draft
                    st.session_state.step2_loaded_version_id = new_selected_id
                    st.session_state.step2_dirty = False
                except Exception as exc:
                    logger.exception("Failed to load version: %s", exc)
                break
        st.rerun()

    # Get resume data
    resume_data = st.session_state.get("step2_draft")
    if not resume_data:
        try:
            resume_data = ResumeData.model_validate_json(selected_version.resume_json)
        except Exception as exc:
            logger.exception("Failed to parse resume data: %s", exc)
            st.error("Failed to load resume data")
            return

    # Check if dirty
    is_dirty = st.session_state.get("step2_dirty", False)

    # Check if selected version is canonical (pinned)
    selected_is_canonical = (
        selected_version.id is not None
        and canonical_version_id is not None
        and selected_version.id == canonical_version_id
    )

    # Row 2: Action buttons
    with st.container(horizontal=True, horizontal_alignment="right"):
        if is_dirty and not show_pdf:
            # Show Discard and Save when there are unsaved changes (only in content tab)
            if st.button("Discard", key=f"step2_discard_changes_{tab_suffix}"):
                # Reload from selected version
                try:
                    original_draft = ResumeData.model_validate_json(selected_version.resume_json)
                    st.session_state.step2_draft = original_draft
                    st.session_state.step2_dirty = False
                    st.rerun()
                except Exception as exc:
                    logger.exception("Failed to discard changes: %s", exc)
                    st.error("Failed to discard changes")

            if st.button("Save", type="primary", key=f"step2_save_changes_{tab_suffix}"):
                try:
                    new_version_id = JobIntakeService.save_manual_resume_edit(job_id, selected_version, resume_data)
                    # Update selection
                    st.session_state.step2_selected_version_id = new_version_id
                    st.session_state.step2_draft = resume_data
                    st.session_state.step2_loaded_version_id = new_version_id
                    st.session_state.step2_dirty = False
                    st.toast("Changes saved as new version!")
                    st.rerun()
                except Exception as exc:
                    logger.exception("Failed to save changes: %s", exc)
                    st.error("Failed to save changes")
        else:
            # Show Copy and Download when no unsaved changes or in PDF tab
            # Copy button (icon only)
            if st.button(":material/content_copy:", key=f"step2_copy_{tab_suffix}", help="Copy resume text"):
                try:
                    import pyperclip

                    pyperclip.copy(str(resume_data))
                    st.toast("Copied to clipboard!")
                except Exception as exc:
                    logger.exception("Failed to copy: %s", exc)
                    st.error("Failed to copy to clipboard")

            # Download button (text only, enabled only when pinned, primary button)
            download_help = None if selected_is_canonical else "Pin this version to enable download"
            try:
                pdf_bytes = ResumeService.render_preview(job_id, resume_data, selected_version.template_name)
                job = JobService.get_job(job_id)
                filename = build_resume_download_filename(job.company_name, job.job_title, resume_data.name)

                st.download_button(
                    label="Download",
                    data=pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    disabled=not selected_is_canonical,
                    type="primary",
                    help=download_help,
                    key=f"step2_download_{tab_suffix}",
                )
            except Exception as exc:
                logger.exception("Failed to render PDF: %s", exc)
                st.button("Download", disabled=True, type="primary", key=f"step2_download_disabled_{tab_suffix}")

    # Show content based on tab type
    if show_pdf:
        # PDF preview
        try:
            pdf_bytes = ResumeService.render_preview(job_id, resume_data, selected_version.template_name)
            pdf_viewer(pdf_bytes, zoom_level="auto")
        except Exception as exc:
            logger.exception("Failed to render PDF: %s", exc)
            st.error("Failed to render PDF preview")
    else:
        # Edit mode with expandable sections
        _render_edit_mode(job_id, selected_version)


def _render_edit_mode(job_id: int, selected_version) -> None:
    """Render edit mode with expandable sections.

    Args:
        job_id: Job ID
        selected_version: Current resume version
    """
    # Get draft from session state
    draft = st.session_state.get("step2_draft")
    if not draft:
        st.error("No resume draft available")
        return

    # Make job id available to add-object dialogs
    st.session_state["current_job_id"] = job_id

    # Render sections (same as resume tab)
    updated = _render_profile_section(draft)
    updated = _render_experience_section(updated)
    updated = _render_education_section(updated)
    updated = _render_certifications_section(updated)
    updated = _render_skills_section(updated)

    # Check if dirty (compare with originally loaded version)
    original_draft = None
    try:
        original_draft = ResumeData.model_validate_json(selected_version.resume_json)
    except Exception:
        pass

    if original_draft:
        is_dirty = updated.model_dump_json() != original_draft.model_dump_json()
    else:
        is_dirty = False

    st.session_state.step2_dirty = is_dirty

    # Update draft in session
    st.session_state.step2_draft = updated


# ==================== Edit Mode Section Renderers ====================
# (Copied from resume.py for identical behavior)


def _render_profile_section(draft: ResumeData) -> ResumeData:
    """Render profile section."""
    with st.expander("Profile", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("Full Name", value=draft.name, key="step2_resume_name")
        with c2:
            title = st.text_input("Title :material/smart_toy:", value=draft.title, key="step2_resume_title")

        c3, c4 = st.columns(2)
        with c3:
            email = st.text_input("Email", value=draft.email, key="step2_resume_email")
        with c4:
            phone = st.text_input("Phone Number", value=draft.phone, key="step2_resume_phone")

        linkedin = st.text_input(
            "LinkedIn URL",
            value=draft.linkedin_url,
            key="step2_resume_linkedin",
            help="Optional - https:// prefix not required, will be added automatically",
        )

        summary = st.text_area(
            "Professional Summary :material/smart_toy:",
            value=draft.professional_summary,
            key="step2_resume_summary",
            height=250,
        )

    return draft.model_copy(
        update={
            "name": name,
            "title": title,
            "email": email,
            "phone": phone,
            "linkedin_url": linkedin,
            "professional_summary": summary,
        }
    )


def _render_experience_section(draft: ResumeData) -> ResumeData:
    """Render experience section."""
    new_experiences: list[ResumeExperience] = []
    deletion_happened = False
    with st.expander("Experience", expanded=False):
        for idx, exp in enumerate(draft.experience):
            with st.container(border=True):
                row1 = st.columns([2, 2, 0.3])
                with row1[0]:
                    etitle = st.text_input("Title", value=exp.title, key=f"step2_exp_title_{idx}")
                with row1[1]:
                    company = st.text_input("Company", value=exp.company, key=f"step2_exp_company_{idx}")
                with row1[2]:
                    del_exp = st.button(":material/delete:", key=f"step2_exp_delete_{idx}", help="Delete experience")

                location = st.text_input("Location", value=exp.location, key=f"step2_exp_location_{idx}")

                row2 = st.columns([2, 2])
                with row2[0]:
                    start_dt = st.date_input(
                        "Start Date",
                        value=exp.start_date,
                        min_value=MIN_DATE,
                        key=f"step2_exp_start_{idx}",
                    )
                with row2[1]:
                    end_dt = st.date_input(
                        "End Date (optional)",
                        value=exp.end_date,
                        min_value=MIN_DATE,
                        key=f"step2_exp_end_{idx}",
                    )

                points_text = st.text_area(
                    ":material/smart_toy: Points (one per line)",
                    value="\n".join(exp.points or []),
                    key=f"step2_exp_{idx}_points_text",
                    height=350,
                    help="Each non-empty line becomes a separate point.",
                )
                new_points: list[str] = [ln.strip() for ln in (points_text or "").splitlines() if ln.strip()]

                if not del_exp:
                    new_experiences.append(
                        ResumeExperience(
                            title=etitle,
                            company=company,
                            location=location,
                            start_date=start_dt,
                            end_date=end_dt,
                            points=[p for p in new_points if p.strip()],
                        )
                    )
                else:
                    deletion_happened = True

        if st.button("Add Experience", key="step2_add_experience"):
            show_resume_add_experience_dialog()

    if deletion_happened:
        try:
            st.session_state["step2_draft"] = draft.model_copy(update={"experience": new_experiences})
            # Clear experience-related widget state
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith("step2_exp_"):
                    st.session_state.pop(key, None)
        except Exception as exc:
            logger.exception("Failed to delete experience: %s", exc)
        st.rerun()

    return draft.model_copy(update={"experience": new_experiences})


def _render_education_section(draft: ResumeData) -> ResumeData:
    """Render education section."""
    new_education: list[ResumeEducation] = []
    deletion_happened = False
    with st.expander("Education", expanded=False):
        for idx, edu in enumerate(draft.education):
            with st.container(border=True):
                row1 = st.columns([2, 2, 0.3])
                with row1[0]:
                    inst = st.text_input("Institution", value=edu.institution, key=f"step2_edu_inst_{idx}")
                with row1[1]:
                    deg = st.text_input("Degree", value=edu.degree, key=f"step2_edu_deg_{idx}")
                with row1[2]:
                    del_edu = st.button(":material/delete:", key=f"step2_edu_delete_{idx}", help="Delete education")

                major = st.text_input("Major", value=edu.major, key=f"step2_edu_maj_{idx}")

                grad_dt = st.date_input(
                    "Graduation Date",
                    value=edu.grad_date,
                    min_value=MIN_DATE,
                    key=f"step2_edu_grad_{idx}",
                )

                if not del_edu:
                    new_education.append(
                        ResumeEducation(
                            degree=deg,
                            major=major,
                            institution=inst,
                            grad_date=grad_dt,
                        )
                    )
                else:
                    deletion_happened = True

        if st.button("Add Education", key="step2_add_education"):
            show_resume_add_education_dialog()

    if deletion_happened:
        try:
            st.session_state["step2_draft"] = draft.model_copy(update={"education": new_education})
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith("step2_edu_"):
                    st.session_state.pop(key, None)
        except Exception as exc:
            logger.exception("Failed to delete education: %s", exc)
        st.rerun()

    return draft.model_copy(update={"education": new_education})


def _render_certifications_section(draft: ResumeData) -> ResumeData:
    """Render certifications section."""
    new_certs: list[ResumeCertification] = []
    deletion_happened = False
    with st.expander("Certificates", expanded=False):
        for idx, cert in enumerate(draft.certifications):
            with st.container(border=True):
                row = st.columns([3, 2, 0.3])
                with row[0]:
                    title = st.text_input("Title", value=cert.title, key=f"step2_cert_title_{idx}")
                with row[1]:
                    date_dt = st.date_input(
                        "Date",
                        value=cert.date,
                        min_value=MIN_DATE,
                        key=f"step2_cert_date_{idx}",
                    )
                with row[2]:
                    del_cert = st.button(
                        ":material/delete:", key=f"step2_cert_delete_{idx}", help="Delete certification"
                    )

                if not del_cert:
                    new_certs.append(ResumeCertification(title=title, date=date_dt))
                else:
                    deletion_happened = True

        if st.button("Add Certification", key="step2_add_cert"):
            show_resume_add_certificate_dialog()

    if deletion_happened:
        try:
            st.session_state["step2_draft"] = draft.model_copy(update={"certifications": new_certs})
            for key in list(st.session_state.keys()):
                if isinstance(key, str) and key.startswith("step2_cert_"):
                    st.session_state.pop(key, None)
        except Exception as exc:
            logger.exception("Failed to delete certification: %s", exc)
        st.rerun()

    return draft.model_copy(update={"certifications": new_certs})


def _render_skills_section(draft: ResumeData) -> ResumeData:
    """Render skills section."""
    with st.expander("Skills :material/smart_toy:", expanded=False):
        skills_text = st.text_area(
            "Skills (accepts commas and/or newlines; formatted one per line)",
            value="\n".join(draft.skills),
            key="step2_resume_skills_textarea",
            height=400,
        )
        # Accept commas, newlines, or a mix
        raw_parts = re.split(r"[\n,]+", skills_text or "")
        skills_list = [part.strip() for part in raw_parts if part and part.strip()]

    return draft.model_copy(update={"skills": skills_list})


# ==================== Completion Functions ====================


def _clear_step2_state(job_id: int) -> None:
    """Clear step 2 state and resume tab state.

    Args:
        job_id: Job ID.
    """
    # Clear step 2 state
    for key in list(st.session_state.keys()):
        if key.startswith("step2_"):
            st.session_state.pop(key, None)

    # Clear resume tab state
    _clear_resume_tab_state(job_id)

    # Clear intake flow state to prevent reopening on return to home
    _clear_intake_flow_state()


def _invoke_resume_tool(tool_call: dict) -> str:
    """Invoke the actual tool function and return its result.

    Args:
        tool_call: Tool call dict with 'name', 'args', and 'id'.

    Returns:
        Tool result message from the actual tool function.
    """
    from app.services.job_intake_service.workflows.resume_refinement import propose_resume_draft

    tool_name = tool_call.get("name", "")
    args = tool_call.get("args", {})

    # Currently only one tool for resume refinement
    if tool_name == "propose_resume_draft":
        try:
            # Get the job context from session state
            job_id = st.session_state.get("intake_job_id")
            selected_version_id = st.session_state.get("step2_selected_version_id")

            if not job_id or not selected_version_id:
                return "Error: Missing job or version context"

            # Get job and version details
            job = JobService.get_job(job_id)
            if not job:
                return "Error: Job not found"

            version = ResumeService.get_version(selected_version_id)
            if not version:
                return "Error: Version not found"

            # Add injected arguments to the args
            args["job_id"] = job.id
            args["user_id"] = job.user_id
            args["template_name"] = version.template_name
            args["parent_version_id"] = version.id
            args["version_tracker"] = {}  # Will be populated by tool

            result = propose_resume_draft.invoke(args)

            # Update selected version if a new one was created
            version_id = args["version_tracker"].get("version_id")
            if version_id:
                st.session_state.step2_selected_version_id = version_id

            return result
        except Exception as exc:
            logger.exception("Error invoking tool %s: %s", tool_name, exc)
            return f"Error executing tool: {str(exc)}"

    # If tool not found, return error
    return f"Unknown tool: {tool_name}"


def _clear_resume_tab_state(job_id: int) -> None:
    """Clear all resume tab session state to ensure clean initialization.

    Clears:
    - Resume draft and template state
    - Dirty flags and saved state
    - Version selection state
    - All resume widget keys (resume_, exp_, edu_, cert_)
    - Resume PDF cache for the specific job

    Args:
        job_id: Job ID for which to clear state
    """
    # Clear main resume state keys
    resume_state_keys = [
        "resume_draft",
        "resume_template",
        "resume_last_saved",
        "resume_template_saved",
        "resume_dirty",
        "resume_selected_version_id",
        "resume_loaded_from_version_id",
        "resume_instructions",
    ]
    for key in resume_state_keys:
        st.session_state.pop(key, None)

    # Clear all widget keys for resume, experience, education, and certifications
    widget_prefixes = ("resume_", "exp_", "edu_", "cert_")
    for key in list(st.session_state.keys()):
        if isinstance(key, str) and key.startswith(widget_prefixes):
            st.session_state.pop(key, None)

    # Clear resume PDF cache for this job
    cache_root = st.session_state.get("resume_pdf_cache")
    if isinstance(cache_root, dict) and job_id in cache_root:
        cache_root.pop(job_id, None)


def _clear_intake_flow_state() -> None:
    """Clear all intake flow session state to prevent dialog from reopening.

    This ensures that when the user returns to the home page after completing
    or closing the intake dialog, it doesn't try to reopen with the old job.
    """
    intake_keys = [
        "intake_job_id",
        "current_step",
        "intake_initial_title",
        "intake_initial_company",
        "intake_initial_description",
    ]
    for key in intake_keys:
        st.session_state.pop(key, None)
