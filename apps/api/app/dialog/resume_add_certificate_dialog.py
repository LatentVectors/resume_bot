"""Dialog for adding a new Certificate item to the in-memory resume draft."""

from __future__ import annotations

from datetime import date
from typing import cast

import streamlit as st

from app.constants import MIN_DATE
from app.services.resume_service import ResumeService
from src.features.resume.types import ResumeCertification, ResumeData
from src.logging_config import logger


def _append_and_refresh(new_cert: ResumeCertification) -> None:
    try:
        draft = cast(ResumeData, st.session_state.get("resume_draft"))
        if draft is None:
            st.error("No resume draft is loaded.")
            return

        updated = draft.model_copy(update={"certifications": [*draft.certifications, new_cert]})
        st.session_state["resume_draft"] = updated
        st.session_state["resume_dirty"] = True

        job_id = cast(int | None, st.session_state.get("current_job_id"))
        template = cast(str, st.session_state.get("resume_template", "resume_000.html"))
        if job_id:
            try:
                pdf_bytes = ResumeService.render_preview(job_id, updated, template)
                st.session_state["resume_preview_bytes"] = pdf_bytes
                st.session_state.pop("resume_preview_path", None)
            except Exception as exc:  # noqa: BLE001
                logger.exception(exc)
        st.toast("Certificate added. Preview refreshed.")
        st.rerun()
    except Exception as exc:  # noqa: BLE001
        logger.exception(exc)
        st.error("Failed to add certificate.")


@st.dialog("Add Certificate", width="large")
def show_resume_add_certificate_dialog() -> None:
    """Open a dialog to add a new certificate for the resume draft only."""
    with st.form("resume_add_certificate_form"):
        title = st.text_input("Title *")
        date_dt = st.date_input("Date *", value=date.today(), min_value=MIN_DATE)

        with st.container(horizontal=True, horizontal_alignment="right"):
            cancel = st.form_submit_button("Cancel")
            submit = st.form_submit_button("Save", type="primary")

        if submit:
            if not title.strip():
                st.error("Title is required.")
            else:
                _append_and_refresh(ResumeCertification(title=title.strip(), date=date_dt))

        if cancel:
            st.rerun()
