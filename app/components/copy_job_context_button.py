"""Reusable copy button component for copying job context to clipboard."""

from __future__ import annotations

from typing import Literal

import streamlit as st

from app.services.experience_service import ExperienceService
from app.services.job_service import JobService
from app.shared.formatters import format_all_experiences
from src.database import db_manager
from src.logging_config import logger


def render_copy_job_context_button(
    job_id: int, button_type: Literal["primary", "secondary", "tertiary"] = "secondary"
) -> None:
    """Render a copy button that copies job context to clipboard.

    The copied content includes:
    - Work experience (formatted with achievements)
    - Job description
    - Gap analysis
    - Stakeholder analysis

    Args:
        job_id: The ID of the job to copy context for.
        button_type: The Streamlit button type (primary, secondary, or tertiary).
            Defaults to "secondary" (Streamlit's default).
    """
    if st.button(
        "",
        key=f"copy_job_context_{job_id}",
        icon=":material/content_copy:",
        help="Copy job context (work experience, job description, analyses)",
        type=button_type,
    ):
        try:
            import importlib

            pyperclip = importlib.import_module("pyperclip")

            # Get job
            job = JobService.get_job(job_id)
            if not job:
                st.error("Job not found.")
                return

            # Get intake session for analyses
            session = JobService.get_intake_session(job_id)

            # Get user's work experience
            experiences = ExperienceService.list_user_experiences(job.user_id)

            # Fetch achievements for each experience
            achievements_by_exp: dict[int, list] = {}
            for exp in experiences:
                achievements = db_manager.list_experience_achievements(exp.id)
                achievements_by_exp[exp.id] = achievements

            work_experience = format_all_experiences(experiences, achievements_by_exp)

            # Get job description
            job_description = job.job_description or ""

            # Get analyses (may be None if not yet created)
            gap_analysis = session.gap_analysis if session else ""
            stakeholder_analysis = session.stakeholder_analysis if session else ""

            # Build the formatted prompt
            prompt = f"""<work_experience>
{work_experience}
</work_experience>

<job_description>
{job_description}
</job_description>

<gap_analysis>
{gap_analysis}
</gap_analysis>

<stakeholder_analysis>
{stakeholder_analysis}
</stakeholder_analysis>
"""

            pyperclip.copy(prompt)
            st.toast("Job context copied to clipboard!", icon=":material/check_circle:")
        except Exception as exc:  # noqa: BLE001
            logger.exception(exc)
            st.error("Failed to copy to clipboard.")
