from __future__ import annotations

from enum import Enum

import streamlit as st

from app.components.status_badge import render_status_badge
from app.services.experience_service import ExperienceService
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from app.services.user_service import UserService
from app.shared.filenames import build_resume_download_filename
from app.shared.formatters import format_all_experiences
from src.database import Job as DbJob
from src.features.resume.types import ResumeData
from src.logging_config import logger

from .utils import fmt_date


def _build_download_filename(job: DbJob, full_name: str) -> str:
    """Builds: "Resume - {company} - {title} - {name} - {yyyy_mm_dd}.pdf"""
    return build_resume_download_filename(job.company_name, job.job_title, full_name)


def render_overview(job: DbJob) -> None:
    """Render the Overview tab for a job per spec."""
    # Editing state and widget keys
    is_editing = st.session_state.get("job_overview_editing", False)
    status_options = ["Saved", "Applied", "Interviewing", "Not Selected", "No Offer", "Hired"]
    title_key = f"overview_title_{job.id}"
    company_key = f"overview_company_{job.id}"
    desc_key = f"overview_description_{job.id}"
    status_key = f"overview_status_{job.id}"

    # Normalize job.status to a label the selectbox understands
    status_value = job.status.value if hasattr(job.status, "value") else str(job.status)
    status_value = status_value if status_value in status_options else "Saved"

    if is_editing:
        with st.form(f"overview_form_{job.id}", clear_on_submit=False):
            header = st.columns([2, 2, 1])
            with header[0]:
                is_favorite = job.is_favorite
                st.text_input(
                    "Title",
                    key=title_key,
                    label_visibility="collapsed",
                    placeholder="Title",
                )
            with header[1]:

                def format_func(status: str | Enum) -> str:
                    if isinstance(status, str):
                        return status
                    return status.value

                st.selectbox(
                    "Status",
                    options=status_options,
                    key=status_key,
                    label_visibility="collapsed",
                    format_func=format_func,
                )
            with header[2]:
                with st.container(horizontal=True, horizontal_alignment="right"):
                    save_clicked = st.form_submit_button("Save", type="primary")
                    discard_clicked = st.form_submit_button("Discard", type="secondary")

            row2 = st.columns([2, 2, 2])
            with row2[0]:
                st.text_input(
                    "Company",
                    key=company_key,
                    label_visibility="collapsed",
                    placeholder="Company",
                )
            with row2[1]:
                dt_created = fmt_date(job.created_at)
                st.write(f"Created: {dt_created}")
            with row2[2]:
                dt_applied = fmt_date(job.applied_at)
                st.write(f"Applied: {dt_applied}")

            st.markdown("---")
            st.text_area(
                "Description",
                key=desc_key,
                height=200,
            )

            if discard_clicked:
                st.session_state["job_overview_editing"] = False
                for k in (title_key, company_key, desc_key, status_key):
                    st.session_state.pop(k, None)
                st.rerun()

            if save_clicked:
                new_title = (st.session_state.get(title_key) or (job.job_title or "")).strip()
                new_company = (st.session_state.get(company_key) or (job.company_name or "")).strip()
                new_description = (
                    st.session_state.get(desc_key)
                    if st.session_state.get(desc_key) is not None
                    else (job.job_description or "")
                )
                new_status = st.session_state.get(status_key) or job.status

                updated = JobService.update_job_fields(
                    job.id,
                    title=new_title,
                    company=new_company,
                    job_description=new_description,
                )
                if updated:
                    if new_status != job.status:
                        JobService.set_status(job.id, new_status)  # type: ignore[arg-type]
                    st.session_state["job_overview_editing"] = False
                    for k in (title_key, company_key, desc_key, status_key):
                        st.session_state.pop(k, None)
                    st.rerun()
                else:
                    st.error("Failed to save changes.")
    else:
        # Header row (view mode)
        header = st.columns([1, 1, 1])
        with header[0]:
            is_favorite = job.is_favorite
            title = f"{job.job_title or '—'}"
            if is_favorite:
                title = f":material/star: {title}"
            st.subheader(title)
        with header[1]:
            render_status_badge(job.status)
        with header[2]:
            with st.container(horizontal=True, horizontal_alignment="right", gap=None):
                if st.button("", key="overview_edit", icon=":material/edit:", help="Edit"):
                    st.session_state["job_overview_editing"] = True
                    st.session_state[title_key] = job.job_title or ""
                    st.session_state[company_key] = job.company_name or ""
                    st.session_state[desc_key] = job.job_description or ""
                    st.session_state[status_key] = status_value
                    st.rerun()

        # Second row (view mode)
        row2 = st.columns([2, 2, 2])
        with row2[0]:
            st.write(job.company_name or "—")
        with row2[1]:
            dt_created = fmt_date(job.created_at)
            st.write(f"Created: {dt_created}")
        with row2[2]:
            dt_applied = fmt_date(job.applied_at)
            st.write(f"Applied: {dt_applied}")

        st.markdown("---")

        # Main content area (view mode)
        left, right = st.columns([4, 1])
        with left:
            # Description header with copy button
            desc_header = st.columns([4, 1])
            with desc_header[0]:
                st.subheader("Description")
            with desc_header[1]:
                if job.job_description:
                    with st.container(horizontal_alignment="right"):
                        if st.button(
                            "",
                            key=f"copy_description_{job.id}",
                            icon=":material/content_copy:",
                            help="Copy job description",
                            type="tertiary",
                        ):
                            st.toast("Job description copied!", icon=":material/check_circle:")

            if job.job_description:
                st.write(job.job_description)
            else:
                st.write("—")

        with right:
            # Favorite toggle
            current_fav = bool(job.is_favorite)
            fav_value = st.toggle("Favorite", value=current_fav, key=f"favorite_toggle_{job.id}")
            if fav_value != current_fav:
                JobService.update_job_fields(job.id, is_favorite=fav_value)
                st.rerun()

            try:
                resume = JobService.get_resume_for_job(job.id)
                if resume and (resume.resume_json or "").strip():
                    # Build display name
                    full_name = ""
                    try:
                        rd = ResumeData.model_validate_json(resume.resume_json)  # type: ignore[arg-type]
                        full_name = (rd.name or "").strip()
                    except Exception:
                        full_name = ""
                    if not full_name:
                        user = UserService.get_current_user()
                        full_name = (
                            f"{(user.first_name if user else '') or ''} {(user.last_name if user else '') or ''}"
                        ).strip()

                    # Fetch canonical bytes and enable download
                    pdf_bytes = ResumeService.render_canonical_pdf_bytes(job.id)
                    st.download_button(
                        label="Download Resume",
                        data=pdf_bytes,
                        file_name=_build_download_filename(job, full_name),
                        mime="application/pdf",
                        type="primary",
                        help="Download the saved resume",
                    )
                else:
                    st.button("Download Resume", disabled=True, help="No resume found")
            except Exception:
                st.button(
                    "Download Resume",
                    disabled=True,
                    help="Unable to render resume. Pin a canonical version or try again.",
                )

            st.button("Download Cover Letter", disabled=True)
            st.button("Copy Cover Letter", disabled=True)

            # Copy Prompt button
            if st.button("Copy Prompt", type="secondary", help="Copy work experience and job description prompt"):
                try:
                    import importlib

                    pyperclip = importlib.import_module("pyperclip")

                    # Get current user and their experiences
                    user = UserService.get_current_user()
                    if user:
                        experiences = ExperienceService.list_user_experiences(user.id)
                        work_experience = format_all_experiences(experiences)
                    else:
                        work_experience = "No work experience available."

                    # Get job description
                    job_description = job.job_description or ""

                    # Build the prompt
                    prompt = f"""<work_experience>
{work_experience}
</work_experience>

<job_description>
{job_description}
</job_description>"""

                    pyperclip.copy(prompt)
                    st.toast("Prompt copied to clipboard!", icon=":material/check_circle:")
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)
                    st.error("Failed to copy to clipboard.")

    # In editing mode, do not render the quick action column on the right
