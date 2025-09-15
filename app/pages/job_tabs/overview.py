from __future__ import annotations

from pathlib import Path

import streamlit as st

from app.services.job_service import JobService
from src.config import settings
from src.logging_config import logger

from .utils import SupportsJob, fmt_datetime, resume_exists


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
        pdf_filename = getattr(job, "resume_filename", "")
        exists = resume_exists(pdf_filename)
        pdf_path: Path | None = (settings.data_dir / "resumes" / pdf_filename).resolve() if exists else None

        if exists and pdf_path is not None:
            try:
                pdf_bytes = pdf_path.read_bytes()
                st.download_button(
                    label="Download Resume PDF",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf",
                    type="primary",
                    key=f"download_resume_{job.id}",
                )
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error preparing resume download for job {job.id}: {e}")
                st.button("Download Resume PDF", disabled=True)
        else:
            st.button("Download Resume PDF", disabled=True, help="No resume file found")

        st.button("Download Cover Letter (disabled)", disabled=True)
        st.button("Copy Cover Letter (disabled)", disabled=True)
