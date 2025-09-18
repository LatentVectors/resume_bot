"""Dialog for adding a new Education item to the in-memory resume draft."""

from __future__ import annotations

from datetime import date
from typing import cast

import streamlit as st

from app.constants import MIN_DATE
from app.services.resume_service import ResumeService
from src.features.resume.types import ResumeData, ResumeEducation
from src.logging_config import logger


def _append_and_refresh(new_education: ResumeEducation) -> None:
    try:
        draft = cast(ResumeData, st.session_state.get("resume_draft"))
        if draft is None:
            st.error("No resume draft is loaded.")
            return

        updated = draft.model_copy(update={"education": [*draft.education, new_education]})
        st.session_state["resume_draft"] = updated
        st.session_state["resume_dirty"] = True

        job_id = cast(int | None, st.session_state.get("current_job_id"))
        template = cast(str, st.session_state.get("resume_template", "resume_000.html"))
        if job_id:
            try:
                preview_path = ResumeService.render_preview(job_id, updated, template)
                st.session_state["resume_preview_path"] = str(preview_path)
            except Exception as exc:  # noqa: BLE001
                logger.exception(exc)
        st.toast("Education added. Preview refreshed.")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        st.error("Failed to add education.")


@st.dialog("Add Education", width="large")
def show_resume_add_education_dialog() -> None:
    """Open a dialog to add a new education item for the resume draft only."""
    with st.form("resume_add_education_form"):
        # Row 1: Institution
        institution = st.text_input("Institution *")

        # Row 2: Degree | Major
        c1, c2 = st.columns([2, 2])
        with c1:
            degree = st.text_input("Degree *")
        with c2:
            major = st.text_input("Major")

        # Row 3: Grad Date
        d1, _ = st.columns([2, 2])
        with d1:
            grad_dt = st.date_input("Graduation Date *", value=date.today(), min_value=MIN_DATE)

        with st.container(horizontal=True, horizontal_alignment="right"):
            cancel = st.form_submit_button("Cancel")
            submit = st.form_submit_button("Save", type="primary")

        if submit:
            if not institution.strip() or not degree.strip():
                st.error("Institution and Degree are required.")
            else:
                _append_and_refresh(
                    ResumeEducation(
                        institution=institution.strip(),
                        degree=degree.strip(),
                        major=major.strip(),
                        grad_date=grad_dt.strftime("%Y-%m-%d"),
                    )
                )

        if cancel:
            st.rerun()
