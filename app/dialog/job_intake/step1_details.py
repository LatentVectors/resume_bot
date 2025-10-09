"""Step 1: Job details confirmation."""

from __future__ import annotations

import streamlit as st

from app.services.job_service import JobService
from src.logging_config import logger


def render_step1_details(
    initial_title: str | None,
    initial_company: str | None,
    initial_description: str,
) -> None:
    """Render Step 1: Job details confirmation.

    Args:
        initial_title: Pre-filled job title from extraction.
        initial_company: Pre-filled company from extraction.
        initial_description: Job description text.
    """
    # Progress indicator
    st.caption("Step 1 of 3: Job Details")
    st.markdown("---")

    # Form fields
    col1, col2 = st.columns(2)
    with col1:
        title = st.text_input(
            "Job Title *",
            value=initial_title or "",
            help="Required",
            key="intake_step1_title",
        )
    with col2:
        company = st.text_input(
            "Company Name *",
            value=initial_company or "",
            help="Required",
            key="intake_step1_company",
        )

    description = st.text_area(
        "Job Description *",
        value=initial_description or "",
        height=200,
        help="Required",
        key="intake_step1_description",
    )

    favorite = st.toggle("Favorite", value=False, key="intake_step1_favorite")

    # Next button (enabled only when required fields filled)
    next_disabled = not (title.strip() and company.strip() and description.strip())

    st.markdown("---")
    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Next", type="primary", disabled=next_disabled, key="intake_step1_next"):
            try:
                # Save job with extraction
                job = JobService.save_job_with_extraction(
                    description=description.strip(),
                    favorite=favorite,
                )
                # Update with user-provided title and company
                JobService.update_job_fields(
                    job.id,
                    title=title.strip(),
                    company=company.strip(),
                )

                # Create intake session
                session = JobService.create_intake_session(job.id)

                # Store job_id for subsequent steps
                st.session_state.intake_job_id = job.id

                # Mark step 1 as completed and move to step 2
                JobService.update_session_step(session.id, step=2, completed=False)

                # Update current step and rerun
                st.session_state.current_step = 2
                st.rerun()

            except Exception as exc:  # noqa: BLE001
                st.error("Failed to save job. Please try again.")
                logger.exception("Failed to save job in intake flow: %s", exc)
