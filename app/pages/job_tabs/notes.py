from __future__ import annotations

import streamlit as st

from app.services.job_service import JobService
from src.database import Job as DbJob
from src.logging_config import logger

from .utils import fmt_datetime


def render_notes(job: DbJob) -> None:
    """Render the Notes tab for a job."""
    st.subheader("Notes")
    with st.form(f"add_note_{job.id}"):
        note_text = st.text_area("New note", placeholder="Write a note...", height=120)
        add_clicked = st.form_submit_button("Add Note", type="primary")
        if add_clicked:
            if note_text and note_text.strip():
                try:
                    JobService.add_note(job.id, note_text)
                    st.success("Note added.")
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    logger.exception("Failed to add note for job %s: %s", job.id, e)
                    st.error("Failed to add note.")
            else:
                st.warning("Please enter some text for the note.")

    st.markdown("---")
    notes = JobService.list_notes(job.id)
    if not notes:
        st.info("No notes yet.")
    else:
        for note in notes:
            st.caption(fmt_datetime(getattr(note, "created_at", None)))
            st.write(getattr(note, "content", ""))
            st.markdown("---")
