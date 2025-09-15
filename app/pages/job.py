from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

from app.services.job_service import JobService
from src.config import settings
from src.logging_config import logger


def _fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(dt)


def _badge(has_content: bool) -> str:
    return "🟢" if has_content else "⚪"


def _resume_exists(filename: str | None) -> bool:
    if not filename:
        return False
    try:
        pdf_path = (settings.data_dir / "resumes" / filename).resolve()
        return pdf_path.exists()
    except Exception:
        return False


def main() -> None:
    # Query param handling
    qp = st.query_params
    job_id_param = qp.get("job_id")
    try:
        job_id = int(job_id_param) if job_id_param is not None else None
    except Exception:
        job_id = None

    if not job_id:
        st.error("Unknown or missing job_id. Return to Jobs.")
        st.page_link("pages/jobs.py", label="Back to Jobs", icon="💼")
        return

    job = JobService.get_job(job_id)
    if not job:
        st.error("Job not found. It may have been removed.")
        st.page_link("pages/jobs.py", label="Back to Jobs", icon="💼")
        return

    # Header with basic info
    top = st.columns([4, 2, 2, 2])
    with top[0]:
        st.subheader(f"{job.job_title or '—'} at {job.company_name or '—'}")
    with top[1]:
        st.metric(label="Status", value=job.status)
    with top[2]:
        st.metric(label="Created", value=_fmt_dt(getattr(job, "created_at", None)))
    with top[3]:
        st.metric(label="Applied", value=_fmt_dt(getattr(job, "applied_at", None)))

    st.markdown("---")

    # Tabs with circle badges
    resp_count = JobService.count_job_responses(job.id)
    msg_count = JobService.count_job_messages(job.id)
    resume_badge = _badge(bool(job.has_resume or _resume_exists(getattr(job, "resume_filename", None))))
    cover_badge = _badge(bool(job.has_cover_letter))
    responses_badge = _badge(resp_count > 0)
    messages_badge = _badge(msg_count > 0)

    tab_overview, tab_resume, tab_cover, tab_responses, tab_messages = st.tabs(
        [
            "Overview",
            f"Resume {resume_badge}",
            f"Cover Letter {cover_badge}",
            f"Responses {responses_badge}",
            f"Messages {messages_badge}",
        ]
    )

    # Overview Tab
    with tab_overview:
        left, right = st.columns([3, 2])
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
            exists = _resume_exists(pdf_filename)
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

    # Resume Tab placeholder
    with tab_resume:
        st.info("Resume content will appear here in a future sprint.")

    # Cover Letter Tab placeholder
    with tab_cover:
        st.info("Cover letter content will appear here in a future sprint.")

    # Responses Tab placeholder
    with tab_responses:
        st.info("Responses linked to this job will be listed here.")

    # Messages Tab placeholder
    with tab_messages:
        st.info("Messages linked to this job will be listed here.")


main()
