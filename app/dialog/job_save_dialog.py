"""Dialog for saving a Job from a description with optional extracted fields."""

from __future__ import annotations

import streamlit as st

from app.pages.job_tabs.utils import navigate_to_job
from app.services.job_service import JobService
from src.logging_config import logger


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

    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input("Title *", value=initial_title or "", help="Required", key="save_job_title")
    with col2:
        company = st.text_input("Company *", value=initial_company or "", help="Required", key="save_job_company")

    favorite = st.toggle("Favorite", value=bool(initial_favorite), key="save_job_favorite")
    description = st.text_area(
        "Job Description *", value=initial_description or "", height=200, help="Required", key="save_job_desc"
    )

    left, right = st.columns(2)
    save_disabled = not (title.strip() and company.strip() and description.strip())
    with left:
        if st.button("Save", type="primary", disabled=save_disabled, key="save_job_submit"):
            try:
                job = JobService.save_job_with_extraction(description=description.strip(), favorite=favorite)
                JobService.update_job_fields(job.id, title=title.strip(), company=company.strip())

                st.success("Job saved!")
                if st.button("Open Job", icon=":material/search:", use_container_width=False, key="open_job_btn"):
                    navigate_to_job(int(job.id))
            except Exception as exc:  # noqa: BLE001
                st.error("Failed to save job. Please try again.")
                logger.error(f"Save Job failed: {exc}")
    with right:
        if st.button("Cancel", key="save_job_cancel"):
            st.rerun()
