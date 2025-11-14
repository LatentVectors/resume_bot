"""Dialog for adding a new Experience item to the in-memory resume draft."""

from __future__ import annotations

from datetime import date
from typing import cast

import streamlit as st

from app.constants import MIN_DATE
from app.services.resume_service import ResumeService
from src.features.resume.types import ResumeData, ResumeExperience
from src.logging_config import logger


def _append_and_refresh(new_experience: ResumeExperience) -> None:
    """Append experience to session draft, mark dirty, render preview, and rerun."""
    try:
        draft = cast(ResumeData, st.session_state.get("resume_draft"))
        if draft is None:
            st.error("No resume draft is loaded.")
            return

        updated = draft.model_copy(update={"experience": [*draft.experience, new_experience]})
        st.session_state["resume_draft"] = updated
        st.session_state["resume_dirty"] = True

        job_id = cast(int | None, st.session_state.get("current_job_id"))
        template = cast(str, st.session_state.get("resume_template", "resume_000.html"))
        if job_id:
            try:
                pdf_bytes = ResumeService.render_preview(job_id, updated, template)
                st.session_state["resume_preview_bytes"] = pdf_bytes
                # Back-compat: clear any old path-based preview state
                st.session_state.pop("resume_preview_path", None)
            except Exception as exc:  # noqa: BLE001
                logger.exception(exc)
        st.toast("Experience added. Preview refreshed.")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        st.error("Failed to add experience.")


@st.dialog("Add Experience", width="large")
def show_resume_add_experience_dialog() -> None:
    """Open a dialog to add a new experience for the resume draft only."""
    with st.form("resume_add_experience_form"):
        # Row 1: Title | Company
        c1, c2 = st.columns([2, 2])
        with c1:
            title = st.text_input("Title *")
        with c2:
            company = st.text_input("Company *")

        # Row 2: Location
        location = st.text_input("Location")

        # Row 3: Start Date | End Date (optional)
        d1, d2 = st.columns([2, 2])
        with d1:
            start_dt = st.date_input("Start Date *", value=date.today(), min_value=MIN_DATE)
        with d2:
            end_dt = st.date_input("End Date", value=None, min_value=MIN_DATE)

        # Row 4: Points textarea (split by newline → list)
        points_text = st.text_area(
            "Points",
            help="Each non-empty line becomes a separate point.",
            height=160,
        )

        with st.container(horizontal=True, horizontal_alignment="right"):
            cancel = st.form_submit_button("Cancel")
            submit = st.form_submit_button("Save", type="primary")

        if submit:
            if not title.strip() or not company.strip():
                st.error("Title and Company are required.")
            else:
                if end_dt and start_dt > end_dt:
                    st.error("Start date must be before end date.")
                else:
                    # Parse points
                    points = [ln.strip() for ln in (points_text or "").splitlines() if ln.strip()]

                    _append_and_refresh(
                        ResumeExperience(
                            title=title.strip(),
                            company=company.strip(),
                            location=location.strip() if location.strip() else "",
                            start_date=start_dt,
                            end_date=end_dt,
                            points=points,
                        )
                    )

        if cancel:
            st.rerun()
