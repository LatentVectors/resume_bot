from __future__ import annotations

import asyncio
import datetime as dt

import streamlit as st
from streamlit_pdf_viewer import pdf_viewer

from app.api_client.endpoints.cover_letters import CoverLettersAPI
from app.components.info_banner import top_info_banner
from app.constants import MIN_DATE
from app.services.user_service import UserService
from app.shared.filenames import build_cover_letter_download_filename
from src.database import Job as DbJob
from src.features.cover_letter.types import CoverLetterData
from src.logging_config import logger


def _build_download_filename(job: DbJob, full_name: str) -> str:
    """Build download filename for cover letter PDF."""
    return build_cover_letter_download_filename(
        job.company_name or "Unknown Company", job.job_title or "Unknown Title", full_name
    )


def _load_or_seed_draft(job: DbJob) -> tuple[CoverLetterData, str]:
    """Return current draft and template for the job, seeding from DB or profile.

    On first load for a job, prefer persisted CoverLetter JSON; otherwise seed from user profile.
    """
    try:
        if isinstance(st.session_state.get("cover_letter_draft"), CoverLetterData) and isinstance(
            st.session_state.get("cover_letter_template"), str
        ):
            return st.session_state["cover_letter_draft"], st.session_state["cover_letter_template"]  # type: ignore[return-value]

        # Try existing persisted cover letter
        try:
            row = asyncio.run(CoverLettersAPI.get_current(job.id))
            if row and (row.cover_letter_json or "").strip():
                try:
                    draft = CoverLetterData.model_validate_json(row.cover_letter_json)  # type: ignore[arg-type]
                    template = (row.template_name or "cover_000.html").strip() or "cover_000.html"
                    st.session_state["cover_letter_draft"] = draft
                    st.session_state["cover_letter_template"] = template
                    st.session_state["cover_letter_last_saved"] = draft
                    st.session_state["cover_letter_template_saved"] = template
                    st.session_state["cover_letter_dirty"] = False
                    return draft, template
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
        except Exception as exc:  # noqa: BLE001
            # No current cover letter found, continue to seed from profile
            logger.debug(f"No current cover letter found for job {job.id}: {exc}")

        # Seed from user profile
        user = UserService.get_current_user()
        name = f"{user.first_name} {user.last_name}".strip() if user else ""
        email = user.email if user else ""
        phone = user.phone_number if user else ""
        title = job.job_title or ""

        draft = CoverLetterData(
            name=name,
            title=title,
            email=email if email and "@" in email else "user@example.com",  # Provide valid default
            phone=phone,
            date=dt.date.today(),
            body_paragraphs=[],
        )

        template = "cover_000.html"
        st.session_state["cover_letter_draft"] = draft
        st.session_state["cover_letter_template"] = template
        st.session_state["cover_letter_last_saved"] = draft
        st.session_state["cover_letter_template_saved"] = template
        st.session_state["cover_letter_dirty"] = False
        return draft, template
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        # Fallback to minimal valid draft
        draft = CoverLetterData(
            name="",
            title="",
            email="user@example.com",
            phone="",
            date=dt.date.today(),
            body_paragraphs=[],
        )
        return draft, "cover_000.html"


def render_cover(job: DbJob) -> None:
    """Render the Cover Letter tab for a job."""
    job_id = int(job.id)  # type: ignore[arg-type]
    read_only = job.applied_at is not None

    if read_only:
        top_info_banner("Cover letter is locked because job status is Applied", icon=":material/lock:")

    # Load or seed draft
    draft, template = _load_or_seed_draft(job)

    # Update session state
    if "cover_letter_draft" not in st.session_state:
        st.session_state["cover_letter_draft"] = draft
    if "cover_letter_template" not in st.session_state:
        st.session_state["cover_letter_template"] = template
    if "cover_letter_last_saved" not in st.session_state:
        st.session_state["cover_letter_last_saved"] = draft
    if "cover_letter_template_saved" not in st.session_state:
        st.session_state["cover_letter_template_saved"] = template
    if "cover_letter_dirty" not in st.session_state:
        st.session_state["cover_letter_dirty"] = False

    # Load versions
    try:
        versions = asyncio.run(CoverLettersAPI.list_versions(job_id))
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        versions = []

    try:
        canonical = asyncio.run(CoverLettersAPI.get_current(job_id))
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        canonical = None

    # Version selection logic
    selected_version_id = st.session_state.get("cover_letter_selected_version_id")
    loaded_from_version_id = st.session_state.get("cover_letter_loaded_from_version_id")

    # Default to canonical version if exists, else head
    if selected_version_id is None and versions:
        if canonical:
            # Find version matching canonical
            for v in versions:
                if v.cover_letter_id == canonical.id and v.cover_letter_json == canonical.cover_letter_json:
                    selected_version_id = v.id
                    break
        if selected_version_id is None:
            # Default to head (newest)
            selected_version_id = versions[-1].id if versions else None
        st.session_state["cover_letter_selected_version_id"] = selected_version_id

    # Reload draft from selected version if changed
    if selected_version_id and selected_version_id != loaded_from_version_id:
        for v in versions:
            if v.id == selected_version_id:
                try:
                    draft = CoverLetterData.model_validate_json(v.cover_letter_json)
                    template = v.template_name
                    st.session_state["cover_letter_draft"] = draft
                    st.session_state["cover_letter_template"] = template
                    st.session_state["cover_letter_last_saved"] = draft
                    st.session_state["cover_letter_template_saved"] = template
                    st.session_state["cover_letter_dirty"] = False
                    st.session_state["cover_letter_loaded_from_version_id"] = selected_version_id
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                break

    # Two-column layout
    left_col, right_col = st.columns([4, 3])

    with left_col:
        st.subheader("Cover Letter Content")

        # Version navigation controls (always visible, disabled when no versions)
        if not read_only:
            has_versions = len(versions) > 0
            nav_container = st.container(horizontal=True, horizontal_alignment="right")
            with nav_container:
                # Determine canonical version ID
                canonical_version_id = None
                if canonical and has_versions:
                    for v in versions:
                        if v.cover_letter_json == canonical.cover_letter_json:
                            canonical_version_id = v.id
                            break

                # Get current version info
                current_version = (
                    next((v for v in versions if v.id == selected_version_id), None) if has_versions else None
                )
                current_index = int(current_version.version_index) if current_version else 1
                min_index = 1
                max_index = int(versions[-1].version_index) if has_versions and versions else 1

                # Left arrow
                go_left = st.button(
                    ":material/chevron_left:",
                    key="cover_ver_left",
                    disabled=not has_versions or current_index <= min_index,
                    help="Older version",
                )

                # Dropdown of versions in descending order (vN..v1) with pin indicator
                if has_versions:
                    try:
                        versions_desc = sorted(versions, key=lambda v: int(v.version_index), reverse=True)
                    except Exception:
                        versions_desc = list(reversed(versions))

                    labels = []
                    for v in versions_desc:
                        label = f"v{v.version_index}"
                        if canonical_version_id and v.id == canonical_version_id:
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
                        key="cover_version_select",
                        disabled=False,
                    )
                else:
                    # Show disabled dropdown when no versions
                    st.selectbox(
                        "Version",
                        options=["No versions"],
                        index=0,
                        label_visibility="collapsed",
                        key="cover_version_select",
                        disabled=True,
                    )
                    chosen_label = None

                # Right arrow
                go_right = st.button(
                    ":material/chevron_right:",
                    key="cover_ver_right",
                    disabled=not has_versions or current_index >= max_index,
                    help="Newer version",
                )

                # Pin button
                selected_is_canonical = (
                    has_versions
                    and selected_version_id is not None
                    and canonical_version_id is not None
                    and selected_version_id == canonical_version_id
                )
                pin_label = ":material/keep:" if selected_is_canonical else ":material/keep_off:"
                pin_help = "Pinned (canonical)" if selected_is_canonical else "Set selected version as canonical"
                pin_type = "primary" if selected_is_canonical else "secondary"
                pin_clicked = st.button(
                    pin_label, help=pin_help, key="cover_pin_btn", type=pin_type, disabled=not has_versions
                )

                # Handle nav/pin events
                new_selected_id = None
                if has_versions:
                    if go_left:
                        target_index = current_index - 1
                        for v in versions:
                            if int(v.version_index) == target_index:
                                new_selected_id = v.id
                                break
                    elif go_right:
                        target_index = current_index + 1
                        for v in versions:
                            if int(v.version_index) == target_index:
                                new_selected_id = v.id
                                break
                    elif chosen_label:
                        # Dropdown change
                        try:
                            chosen_index = int(chosen_label.replace(" (pinned)", "").removeprefix("v"))
                            if chosen_index != current_index:
                                for v in versions:
                                    if int(v.version_index) == chosen_index:
                                        new_selected_id = v.id
                                        break
                        except Exception:
                            pass

                    if pin_clicked and selected_version_id:
                        try:
                            asyncio.run(CoverLettersAPI.pin_version(job_id, selected_version_id))
                            st.toast("Pinned canonical cover letter.")
                        except Exception as exc:  # noqa: BLE001
                            logger.exception(exc)
                            st.error(f"Failed to set canonical cover letter: {exc}")
                        st.rerun()

                    if new_selected_id is not None:
                        st.session_state["cover_letter_selected_version_id"] = new_selected_id
                        # Reset dirty and baseline to selected version
                        new_v = next((v for v in versions if v.id == new_selected_id), None)
                        if new_v:
                            try:
                                new_draft = CoverLetterData.model_validate_json(new_v.cover_letter_json)
                            except Exception as exc:  # noqa: BLE001
                                logger.exception(exc)
                                new_draft = draft
                            st.session_state["cover_letter_draft"] = new_draft
                            st.session_state["cover_letter_template"] = new_v.template_name
                            st.session_state["cover_letter_last_saved"] = new_draft
                            st.session_state["cover_letter_template_saved"] = new_v.template_name
                            st.session_state["cover_letter_dirty"] = False
                            st.session_state["cover_letter_loaded_from_version_id"] = new_selected_id
                            st.rerun()

        # Template selector (load here for layout and dirty state tracking)
        try:
            available_templates = asyncio.run(CoverLettersAPI.list_templates())
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
            available_templates = ["cover_000.html"]

        if not available_templates:
            available_templates = ["cover_000.html"]

        # Control buttons row + Template dropdown (similar to resume tab)
        cols = st.columns([1, 1])
        if not read_only:
            with cols[0]:
                template_selected = st.selectbox(
                    "Template",
                    options=available_templates,
                    index=(available_templates.index(template) if template in available_templates else 0),
                    key="cover_template_select",
                    label_visibility="collapsed",
                )
        else:
            # Keep previous template when read-only
            template_selected = st.session_state.get("cover_letter_template", template)

        # Header information (collapsible)
        with st.expander("Header Information", expanded=False):
            name = st.text_input("Name", value=draft.name, key="cover_name", disabled=read_only)
            title_input = st.text_input("Title", value=draft.title, key="cover_title", disabled=read_only)
            email = st.text_input("Email", value=draft.email, key="cover_email", disabled=read_only)
            phone_input = st.text_input("Phone", value=draft.phone, key="cover_phone", disabled=read_only)
            date_input = st.date_input(
                "Date", value=draft.date, min_value=MIN_DATE, key="cover_date", disabled=read_only
            )

        # Body paragraphs (collapsible)
        with st.expander("Body Paragraphs", expanded=True):
            body_text = "\n\n".join(draft.body_paragraphs)
            body_paragraphs_input = st.text_area(
                "Body Paragraphs",
                value=body_text,
                height=600,
                placeholder="Enter your cover letter paragraphs here. Separate paragraphs with a blank line.",
                key="cover_body",
                disabled=read_only,
                label_visibility="collapsed",
            )

        # Update draft from inputs
        body_paragraphs_list = [p.strip() for p in body_paragraphs_input.split("\n\n") if p.strip()]

        # Create updated draft
        try:
            updated_draft = CoverLetterData(
                name=name,
                title=title_input,
                email=email if email and "@" in email else draft.email,
                phone=phone_input,
                date=date_input,  # type: ignore[arg-type]
                body_paragraphs=body_paragraphs_list,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
            updated_draft = draft

        # Dirty state tracking
        saved_draft = st.session_state["cover_letter_last_saved"]
        saved_template = st.session_state["cover_letter_template_saved"]
        is_dirty = (
            updated_draft.model_dump_json() != saved_draft.model_dump_json() or template_selected != saved_template
        )
        st.session_state["cover_letter_dirty"] = is_dirty

        # Persist draft and template in session for subsequent runs
        st.session_state["cover_letter_draft"] = updated_draft
        st.session_state["cover_letter_template"] = template_selected

        # Check for missing required fields
        missing_required = not name.strip() or not email.strip() or "@" not in email

        # Save/Discard buttons (after computing draft and dirty state)
        save_clicked = False
        if not read_only:
            with cols[1]:
                with st.container(horizontal=True, horizontal_alignment="right"):
                    if st.button("Discard", disabled=not is_dirty, key="cover_discard_btn"):
                        st.session_state["cover_letter_draft"] = saved_draft
                        st.session_state["cover_letter_template"] = saved_template
                        st.session_state["cover_letter_dirty"] = False
                        st.rerun()
                    save_clicked = st.button(
                        "Save",
                        disabled=(not is_dirty) or missing_required,
                        key="cover_save_btn",
                        type="primary",
                    )

        if missing_required:
            st.warning("Required fields (name, email) must be filled before saving")

        # Separator after controls
        st.markdown("---")

    # Handle save action after rendering to avoid layout jumps
    if save_clicked:
        try:
            new_version = asyncio.run(
                CoverLettersAPI.create_version(
                    job_id=job_id,
                    cover_letter_json=updated_draft.model_dump_json(),
                    template_name=template_selected,
                )
            )
            st.session_state["cover_letter_last_saved"] = updated_draft
            st.session_state["cover_letter_template_saved"] = template_selected
            st.session_state["cover_letter_dirty"] = False
            st.session_state["cover_letter_selected_version_id"] = new_version.id
            st.session_state["cover_letter_loaded_from_version_id"] = new_version.id
            st.success(f"Saved version v{new_version.version_index}!")
            st.rerun()
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to save cover letter: {exc}")
            logger.exception(exc)

    with right_col:
        st.subheader("Preview")

        # Copy and Download buttons row (right-aligned)
        buttons_container = st.container(horizontal=True, horizontal_alignment="right")
        with buttons_container:
            # Copy button
            copy_clicked = st.button(
                ":material/content_copy:",
                help="Copy cover letter text to clipboard",
                key="cover_copy_btn",
            )
            if copy_clicked:
                try:
                    import importlib

                    pyperclip = importlib.import_module("pyperclip")
                    # Format cover letter text
                    cover_text = f"{updated_draft.name}\n"
                    if updated_draft.title:
                        cover_text += f"{updated_draft.title}\n"
                    cover_text += f"{updated_draft.email}\n"
                    if updated_draft.phone:
                        cover_text += f"{updated_draft.phone}\n"
                    cover_text += f"\n{updated_draft.date}\n\n"
                    cover_text += "\n\n".join(updated_draft.body_paragraphs)
                    pyperclip.copy(cover_text)
                    st.toast("Copied!")
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                    st.error("Failed to copy to clipboard.")

            # Download button
            download_disabled = is_dirty or not canonical
            download_pdf_bytes: bytes | None = None
            if canonical and not is_dirty and selected_version_id is not None:
                try:
                    download_pdf_bytes = asyncio.run(CoverLettersAPI.download_pdf(job_id, selected_version_id))
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                    download_pdf_bytes = None

            if download_pdf_bytes:
                filename = _build_download_filename(job, updated_draft.name)
                st.download_button(
                    label="Download",
                    data=download_pdf_bytes,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary",
                    disabled=download_disabled,
                    key="cover_download",
                )
            else:
                st.button("Download", disabled=True, key="cover_download_disabled")

        # PDF preview
        try:
            # Check if required fields are present
            if not updated_draft.name or not updated_draft.email:
                st.info("Fill in required fields (name, email) to see preview")
            else:
                pdf_bytes = asyncio.run(
                    CoverLettersAPI.preview_pdf_draft(job_id, updated_draft, template_selected)
                )
                pdf_viewer(pdf_bytes, zoom_level="auto")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to render PDF preview: {exc}")
            logger.exception(exc)
