"""Step 1: Job details confirmation."""

from __future__ import annotations

import streamlit as st

from app.components.api_quota_error_banner import show_api_quota_error_banner
from app.exceptions import OpenAIQuotaExceededError
from app.services.experience_service import ExperienceService
from app.services.job_intake_service.workflows.gap_analysis import analyze_job_experience_fit
from app.services.job_intake_service.workflows.stakeholder_analysis import analyze_stakeholders
from app.services.job_service import JobService
from app.services.user_service import UserService
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

    # Check if there's an API quota error to display
    if st.session_state.get("step1_api_quota_error", False):
        show_api_quota_error_banner()
        # Clear the error flag after displaying
        st.session_state.step1_api_quota_error = False

    # Check if we're returning from a later step and load existing values
    existing_job_id = st.session_state.get("intake_job_id")
    if existing_job_id:
        existing_job = JobService.get_job(existing_job_id)
        if existing_job:
            initial_title = existing_job.job_title or initial_title
            initial_company = existing_job.company_name or initial_company
            initial_description = existing_job.job_description or initial_description
            favorite_value = existing_job.is_favorite or False
        else:
            favorite_value = False
    else:
        favorite_value = False

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

    favorite = st.toggle("Favorite", value=favorite_value, key="intake_step1_favorite")

    # Next button (enabled only when required fields filled)
    next_disabled = not (title.strip() and company.strip() and description.strip())

    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Next", type="primary", disabled=next_disabled, key="intake_step1_next"):
            try:
                # Check if we're returning from a later step (job already exists)
                existing_job_id = st.session_state.get("intake_job_id")
                
                if existing_job_id:
                    # Returning from later step - check if job details changed
                    existing_job = JobService.get_job(existing_job_id)
                    if existing_job:
                        # Check if any details changed
                        details_changed = (
                            existing_job.job_title != title.strip()
                            or existing_job.company_name != company.strip()
                            or existing_job.job_description != description.strip()
                        )
                        
                        if details_changed:
                            # Update job details
                            JobService.update_job_fields(
                                existing_job_id,
                                title=title.strip(),
                                company=company.strip(),
                                job_description=description.strip(),
                                is_favorite=favorite,
                            )
                            
                            # Clear analyses to force regeneration
                            session = JobService.get_intake_session(existing_job_id)
                            if session:
                                JobService.save_gap_analysis(session.id, "")
                                JobService.save_stakeholder_analysis(session.id, "")
                                logger.info(
                                    "Cleared analyses due to job detail changes for job_id=%s",
                                    existing_job_id
                                )
                        
                        # Use existing job
                        job = JobService.get_job(existing_job_id)
                        if not job:
                            st.error("Failed to load job. Please try again.")
                            return
                        session = JobService.get_intake_session(existing_job_id)
                        if not session:
                            st.error("Failed to load session. Please try again.")
                            return
                    else:
                        # Job not found, create new one
                        job = JobService.save_job(
                            title=title.strip(),
                            company=company.strip(),
                            description=description.strip(),
                            favorite=favorite,
                        )
                        session = JobService.create_intake_session(job.id)
                        st.session_state.intake_job_id = job.id
                else:
                    # First time through - create new job
                    job = JobService.save_job(
                        title=title.strip(),
                        company=company.strip(),
                        description=description.strip(),
                        favorite=favorite,
                    )
                    session = JobService.create_intake_session(job.id)
                    st.session_state.intake_job_id = job.id

                # Get user experiences for analysis
                current_user = UserService.get_current_user()
                if not current_user or not current_user.id:
                    st.error("Unable to load user data. Please try again.")
                    logger.error("No current user found during step 1 completion")
                    return

                experiences = ExperienceService.list_user_experiences(current_user.id)

                # Check and generate analyses individually (only regenerate what's missing)
                gap_analysis = session.gap_analysis
                stakeholder_analysis = session.stakeholder_analysis

                needs_gap = not gap_analysis or not gap_analysis.strip()
                needs_stakeholder = not stakeholder_analysis or not stakeholder_analysis.strip()

                if needs_gap or needs_stakeholder:
                    # Generate only missing analyses
                    spinner_msg = "Analyzing job requirements and stakeholders..."
                    if needs_gap and not needs_stakeholder:
                        spinner_msg = "Analyzing job requirements..."
                    elif needs_stakeholder and not needs_gap:
                        spinner_msg = "Analyzing stakeholders..."

                    with st.spinner(spinner_msg):
                        try:
                            if needs_gap:
                                gap_analysis = analyze_job_experience_fit(job.job_description, experiences)
                                if not gap_analysis or not gap_analysis.strip():
                                    st.error("Unable to load analyses. Please restart intake flow.")
                                    logger.error("Gap analysis failed for job_id=%s", job.id)
                                    return
                                JobService.save_gap_analysis(session.id, gap_analysis)
                                logger.info("Generated gap analysis for job_id=%s", job.id)

                            if needs_stakeholder:
                                stakeholder_analysis = analyze_stakeholders(job.job_description, experiences)
                                if not stakeholder_analysis or not stakeholder_analysis.strip():
                                    st.error("Unable to load analyses. Please restart intake flow.")
                                    logger.error("Stakeholder analysis failed for job_id=%s", job.id)
                                    return
                                JobService.save_stakeholder_analysis(session.id, stakeholder_analysis)
                                logger.info("Generated stakeholder analysis for job_id=%s", job.id)

                        except OpenAIQuotaExceededError:
                            # Set flag to show error banner on next render
                            st.session_state.step1_api_quota_error = True
                            st.rerun()
                            return
                else:
                    # Both analyses already exist
                    logger.info("Reusing existing analyses for job_id=%s", job.id)

                # Mark step 1 as completed and move to step 2
                JobService.update_session_step(session.id, step=2, completed=False)

                # Update current step and rerun
                st.session_state.current_step = 2
                st.rerun()

            except Exception as exc:  # noqa: BLE001
                st.error("Failed to save job. Please try again.")
                logger.exception("Failed to save job in intake flow: %s", exc)
