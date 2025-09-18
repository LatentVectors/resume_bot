from __future__ import annotations

import streamlit as st

from app.services.job_service import JobService
from app.services.user_service import UserService
from app.shared.filenames import build_resume_download_filename
from src.config import settings
from src.features.resume.types import ResumeData

from .utils import SupportsJob, fmt_datetime


def _build_download_filename(job: SupportsJob, full_name: str) -> str:
    """Builds: "Resume - {company} - {title} - {name} - {yyyy_mm_dd}.pdf"""
    return build_resume_download_filename(job.company_name, job.job_title, full_name)


def render_overview(job: SupportsJob) -> None:
    """Render the Overview tab for a job.

    Args:
        job: The job record to display.
    """
    # Header
    top = st.columns([4, 2, 2, 2])
    with top[0]:
        st.subheader(f"{job.job_title or '—'} at {job.company_name or '—'}")
    with top[1]:
        st.metric(label="Status", value=job.status)
    with top[2]:
        st.metric(label="Created", value=fmt_datetime(getattr(job, "created_at", None)))
    with top[3]:
        st.metric(label="Applied", value=fmt_datetime(getattr(job, "applied_at", None)))

    st.markdown("---")

    left, right = st.columns([3, 1])
    with left:
        st.subheader("Description")
        if job.job_description:
            collapsed = st.toggle("Collapse", value=True, key="desc_collapse")
            if collapsed and len(job.job_description) > 500:
                st.write(job.job_description[:500] + "…")
                if st.button("Expand full description", key="expand_desc"):
                    st.session_state["desc_collapse"] = False
                    st.rerun()
            else:
                st.write(job.job_description)
        else:
            st.write("—")

        st.markdown("---")
        st.subheader("Title & Company")

        edit_mode = st.toggle("Edit", value=False, key="edit_meta")
        if edit_mode:
            new_title = st.text_input("Title", value=job.job_title or "")
            new_company = st.text_input("Company", value=job.company_name or "")
            col_a, col_b = st.columns([1, 1])
            with col_a:
                if st.button("Save", type="primary"):
                    updated = JobService.update_job_fields(job.id, title=new_title, company=new_company)
                    if updated:
                        st.success("Saved.")
                        st.rerun()
                    else:
                        st.error("Failed to save changes.")
            with col_b:
                st.button("Cancel")
        else:
            st.write(f"Title: {job.job_title or '—'}")
            st.write(f"Company: {job.company_name or '—'}")

        st.markdown("---")
        st.subheader("Status")
        status = st.selectbox(
            "Select status",
            options=["Saved", "Applied", "Interviewing", "Not Selected", "No Offer", "Hired"],
            index=["Saved", "Applied", "Interviewing", "Not Selected", "No Offer", "Hired"].index(job.status),
        )
        if st.button("Update Status", key="update_status"):
            updated = JobService.set_status(job.id, status)  # type: ignore[arg-type]
            if updated:
                st.success("Status updated.")
                st.rerun()
            else:
                st.error("Failed to update status.")

        st.markdown("---")
        st.subheader("Favorite")
        fav = st.toggle("Mark as favorite", value=bool(job.is_favorite), key="fav_toggle")
        if fav != bool(job.is_favorite):
            updated = JobService.update_job_fields(job.id, is_favorite=fav)
            if updated:
                st.rerun()

    with right:
        st.subheader("Quick Actions")
        resume = JobService.get_resume_for_job(job.id)
        pdf_filename = (getattr(resume, "pdf_filename", None) or "").strip()
        if pdf_filename:
            pdf_path = (settings.data_dir / "resumes" / pdf_filename).resolve()
            if pdf_path.exists():
                with pdf_path.open("rb") as fh:
                    # Prefer the name saved in the resume JSON, fallback to current user profile
                    full_name = ""
                    try:
                        if getattr(resume, "resume_json", None):
                            rd = ResumeData.model_validate_json(resume.resume_json)  # type: ignore[arg-type]
                            full_name = (rd.name or "").strip()
                    except Exception:
                        full_name = ""
                    if not full_name:
                        user = UserService.get_current_user()
                        full_name = (
                            f"{(user.first_name if user else '') or ''} {(user.last_name if user else '') or ''}"
                        ).strip()
                    st.download_button(
                        label="Download Resume PDF",
                        data=fh.read(),
                        file_name=_build_download_filename(job, full_name),
                        mime="application/pdf",
                        type="primary",
                        help="Download the saved resume PDF",
                    )
            else:
                st.button(
                    "Download Resume PDF",
                    disabled=True,
                    help="Resume PDF not found on disk. Try re-saving from the Resume tab.",
                )
        else:
            st.button("Download Resume PDF", disabled=True, help="No resume file found")

        st.button("Download Cover Letter (disabled)", disabled=True)
        st.button("Copy Cover Letter (disabled)", disabled=True)
