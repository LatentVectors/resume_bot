"""Job intake flow dialog with multi-step workflow.

This dialog guides users through a 2-step process:
1. Job details confirmation
2. Experience & resume development (AI-assisted continuous conversation)

This is the main entry point that routes to individual step modules.
"""

from __future__ import annotations

import streamlit as st

from app.dialog.job_intake.step1_details import render_step1_details
from app.dialog.job_intake.step2_experience_and_resume import (
    render_step2_experience_and_resume,
)


@st.dialog("Job Intake", width="large")
def show_job_intake_dialog(
    initial_title: str | None = None,
    initial_company: str | None = None,
    initial_description: str = "",
    job_id: int | None = None,
) -> None:
    """Main intake flow dialog with step-based rendering.

    Uses session_state.current_step to determine which step to render.
    Each step is isolated in its own module file.

    Args:
        initial_title: Pre-filled job title from extraction.
        initial_company: Pre-filled company from extraction.
        initial_description: Job description text.
        job_id: Existing job ID (for resumption).
    """
    # Initialize session state if needed
    if "current_step" not in st.session_state:
        st.session_state.current_step = 1

    # Store initial values in session state for Step 1
    if "intake_initial_title" not in st.session_state:
        st.session_state.intake_initial_title = initial_title
    if "intake_initial_company" not in st.session_state:
        st.session_state.intake_initial_company = initial_company
    if "intake_initial_description" not in st.session_state:
        st.session_state.intake_initial_description = initial_description
    if "intake_job_id" not in st.session_state:
        st.session_state.intake_job_id = job_id

    # Render appropriate step
    if st.session_state.current_step == 1:
        render_step1_details(
            st.session_state.intake_initial_title,
            st.session_state.intake_initial_company,
            st.session_state.intake_initial_description,
        )
    elif st.session_state.current_step == 2:
        render_step2_experience_and_resume(st.session_state.intake_job_id)
