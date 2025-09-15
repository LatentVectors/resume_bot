"""Dialog for saving a Job from a description with optional extracted fields."""

from __future__ import annotations

import streamlit as st

from app.services.job_service import JobService
from src.logging_config import logger
from src.utils.url import build_app_url


@st.dialog("Save Job", width="large")
def show_save_job_dialog(
    *,
    initial_title: str | None,
    initial_company: str | None,
    initial_description: str,
    initial_favorite: bool,
) -> None:
    """Render the Save Job dialog and handle save.

    Args:
        initial_title: Prefilled job title from extraction, can be None.
        initial_company: Prefilled company name from extraction, can be None.
        initial_description: Required job description text.
        initial_favorite: Whether to pre-toggle favorite.
    """
    st.subheader("Confirm Job Details")

    with st.form("save_job_dialog_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Title *", value=initial_title or "", help="Required")
        with col2:
            company = st.text_input("Company *", value=initial_company or "", help="Required")

        favorite = st.toggle("Favorite", value=bool(initial_favorite))
        description = st.text_area("Job Description *", value=initial_description or "", height=200, help="Required")

        left, right = st.columns(2)
        with left:
            save_disabled = not (title.strip() and company.strip() and description.strip())
            if st.form_submit_button("Save", type="primary", disabled=save_disabled):
                if not title.strip() or not company.strip() or not description.strip():
                    st.error("Title, Company, and Job Description are required.")
                else:
                    try:
                        # Create base job (with extraction already applied in service)
                        job = JobService.save_job_with_extraction(description=description.strip(), favorite=favorite)
                        # Ensure user-entered values override extraction if changed
                        JobService.update_job_fields(job.id, title=title.strip(), company=company.strip())

                        # Provide link to Job page with query params
                        st.success("Job saved!")
                        job_url = build_app_url(f"/job?job_id={job.id}")
                        st.page_link(job_url, label="Open Job", icon="🔎", width="content")
                    except Exception as exc:  # noqa: BLE001
                        st.error("Failed to save job. Please try again.")
                        logger.error(f"Save Job failed: {exc}")
        with right:
            if st.form_submit_button("Cancel"):
                st.rerun()
