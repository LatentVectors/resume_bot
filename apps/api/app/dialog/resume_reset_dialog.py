from __future__ import annotations

import streamlit as st

from app.services.job_service import JobService
from src.logging_config import logger


@st.dialog("Reset Resume", width="small")
def show_resume_reset_dialog(job_id: int) -> None:
    """Confirmation dialog to hard-reset the resume for a job.

    Deletes the Resume row (if any) and clears in-memory UI state so the editor
    returns to its initial seeded state. No PDF files are read or written.
    """
    st.warning("This will delete the saved resume and PDFs and reset the editor. This cannot be undone.")

    with st.container(horizontal=True, horizontal_alignment="right"):
        if st.button("Cancel", key="resume_reset_cancel"):
            st.rerun()

        if st.button("Reset", type="primary", key="resume_reset_confirm"):
            try:
                # Delete Resume row if it exists (no PDF files involved)
                try:
                    resume_row = JobService.get_resume_for_job(job_id)
                    if resume_row is not None:
                        JobService.delete_resume(int(resume_row.id))  # type: ignore[arg-type]
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)

                # Clear session state for a clean UI re-seed
                for key in (
                    "resume_draft",
                    "resume_template",
                    "resume_last_saved",
                    "resume_template_saved",
                    "resume_dirty",
                    # legacy session keys removed in bytes-based rendering
                ):
                    try:
                        st.session_state.pop(key, None)
                    except Exception:
                        pass

                # Clear widget keys so inputs reinitialize
                for key in (
                    "resume_title",
                    "resume_summary",
                    "resume_skills_textarea",
                    "resume_instructions",
                ):
                    try:
                        st.session_state.pop(key, None)
                    except Exception:
                        pass

                try:
                    # Clear dynamic experience points textareas
                    for k in list(st.session_state.keys()):
                        if isinstance(k, str) and k.startswith("exp_") and k.endswith("_points_text"):
                            st.session_state.pop(k, None)
                except Exception as exc:  # noqa: BLE001
                    logger.exception(exc)

                st.toast("Resume reset. Start fresh.")
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                logger.exception(exc)
                st.error("Failed to reset resume. See logs.")
