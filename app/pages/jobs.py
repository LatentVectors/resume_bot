"""Jobs page showing generated resumes and details with PDF viewer."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.services.user_service import UserService
from src.config import settings
from src.database import Job as DbJob
from src.database import db_manager
from src.logging_config import logger


def _truncate(text: str, max_len: int = 140) -> str:
    if not text:
        return ""
    text = text.strip()
    return text if len(text) <= max_len else text[: max_len - 1] + "…"


@st.dialog("Job Details", width="large")
def show_job_detail_dialog(job: DbJob) -> None:
    """Display full job details and render the associated PDF resume."""
    st.subheader("Job Description")
    st.write(job.job_description)

    st.markdown("---")
    st.subheader("Resume")

    pdf_path = (settings.data_dir / "resumes" / job.resume_filename).resolve()
    try:
        if not pdf_path.exists():
            st.error(f"PDF file not found: {pdf_path}")
        else:
            pdf_bytes = pdf_path.read_bytes()
            # Use Streamlit's native PDF component (1.38+) with stretch height
            st.pdf(data=pdf_bytes, height="stretch")
            st.download_button(
                label="Download Resume",
                data=pdf_bytes,
                file_name=job.resume_filename,
                mime="application/pdf",
                type="primary",
                key=f"download_job_{job.id}",
            )
    except Exception as e:  # noqa: BLE001
        st.error("Failed to display PDF.")
        logger.error(f"Error displaying PDF '{pdf_path}': {e}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"Filename: {job.resume_filename}")
    with col2:
        created_str = (
            job.created_at.strftime("%Y-%m-%d %H:%M:%S")
            if isinstance(job.created_at, datetime)
            else str(job.created_at)
        )
        st.caption(f"Created: {created_str}")

    if st.button("Close"):
        st.rerun()


def main() -> None:
    st.title("💼 Jobs")

    user = UserService.get_current_user()
    if not user:
        st.error("No user found. Please complete onboarding first.")
        return

    try:
        jobs = db_manager.list_jobs_by_user_id(user.id)
    except Exception as e:  # noqa: BLE001
        st.error("Failed to load jobs. Please try again later.")
        logger.error(f"Error listing jobs for user {user.id}: {e}")
        return

    if not jobs:
        st.info("No jobs found yet. Generate a resume from the Home page to see it here.")
        return

    st.markdown("---")
    st.subheader("Job Applications")

    # Header row
    header_cols = st.columns([5, 2, 2, 2, 1, 1])
    with header_cols[0]:
        st.markdown("**Job Description**")
    with header_cols[1]:
        st.markdown("**Company**")
    with header_cols[2]:
        st.markdown("**Job Title**")
    with header_cols[3]:
        st.markdown("**Created Date**")
    with header_cols[4]:
        st.markdown("**View**")
    with header_cols[5]:
        st.markdown('<div style="text-align:center"><strong>⬇️</strong></div>', unsafe_allow_html=True)

    # Rows (already newest-first from DB)
    for job in jobs:
        cols = st.columns([5, 2, 2, 2, 1, 1])
        with cols[0]:
            st.write(_truncate(job.job_description, 180))
        with cols[1]:
            st.write(job.company_name or "—")
        with cols[2]:
            st.write(job.job_title or "—")
        with cols[3]:
            created_str = (
                job.created_at.strftime("%Y-%m-%d %H:%M:%S")
                if isinstance(job.created_at, datetime)
                else str(job.created_at)
            )
            st.write(created_str)
        with cols[4]:
            if st.button("View", key=f"view_job_{job.id}"):
                show_job_detail_dialog(job)
        with cols[5]:
            try:
                if not getattr(job, "resume_filename", None):
                    st.download_button(
                        label="⬇️",
                        data=b"",
                        file_name="resume.pdf",
                        mime="application/pdf",
                        disabled=True,
                        help="Download PDF",
                        key=f"download_job_row_{job.id}",
                    )
                else:
                    pdf_path = (settings.data_dir / "resumes" / job.resume_filename).resolve()
                    if not pdf_path.exists():
                        st.download_button(
                            label="⬇️",
                            data=b"",
                            file_name=job.resume_filename or "resume.pdf",
                            mime="application/pdf",
                            disabled=True,
                            help="Download PDF",
                            key=f"download_job_row_{job.id}",
                        )
                    else:
                        pdf_bytes = pdf_path.read_bytes()
                        st.download_button(
                            label="⬇️",
                            data=pdf_bytes,
                            file_name=job.resume_filename,
                            mime="application/pdf",
                            type="primary",
                            help="Download PDF",
                            key=f"download_job_row_{job.id}",
                        )
            except Exception as e:  # noqa: BLE001
                logger.error(f"Error rendering download for job {job.id}: {e}")
                st.download_button(
                    label="⬇️",
                    data=b"",
                    file_name=job.resume_filename or "resume.pdf",
                    mime="application/pdf",
                    disabled=True,
                    help="Download PDF",
                    key=f"download_job_row_{job.id}",
                )


main()
