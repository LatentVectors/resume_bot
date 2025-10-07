from enum import StrEnum

import streamlit as st

from app.pages.job_tabs import (
    badge as _badge,
)
from app.pages.job_tabs import (
    render_cover,
    render_messages,
    render_notes,
    render_overview,
    render_responses,
    render_resume,
)
from app.services.job_service import JobService


class JobTab(StrEnum):
    OVERVIEW = "Overview"
    RESUME = "Resume"
    COVER = "Cover Letter"
    RESPONSES = "Responses"
    MESSAGES = "Messages"
    NOTES = "Notes"


def main() -> None:
    # Session-state based routing
    job_id = st.session_state.get("selected_job_id")
    if not isinstance(job_id, int):
        st.error("No job selected. Return to Jobs.")
        st.page_link("pages/jobs.py", label="Back to Jobs", icon=":material/work:")
        return

    # Reset resume and cover letter PDF caches when navigating to a different job
    try:
        last_job_id = st.session_state.get("_last_job_id")
        if last_job_id != job_id:
            # Clear the entire cache root or the previous job's bucket to avoid stale entries
            resume_cache_root = st.session_state.get("resume_pdf_cache")
            if isinstance(resume_cache_root, dict):
                # Remove all cached buckets to ensure a clean slate, per requirement
                st.session_state["resume_pdf_cache"] = {}
            cover_cache_root = st.session_state.get("cover_letter_pdf_cache")
            if isinstance(cover_cache_root, dict):
                st.session_state["cover_letter_pdf_cache"] = {}
            st.session_state["_last_job_id"] = job_id
    except Exception:
        # Non-fatal if session_state not accessible
        st.session_state["_last_job_id"] = job_id

    job = JobService.get_job(job_id)
    if not job:
        st.error("Job not found. It may have been removed.")
        st.page_link("pages/jobs.py", label="Back to Jobs", icon=":material/work:")
        return

    # Segmented control options with badges
    resp_count = JobService.count_job_responses(job.id)
    msg_count = JobService.count_job_messages(job.id)
    notes_count = JobService.count_job_notes(job.id)

    resume_badge = _badge(bool(job.has_resume))
    cover_badge = _badge(bool(job.has_cover_letter))
    responses_badge = _badge(resp_count > 0)
    messages_badge = _badge(msg_count > 0)
    notes_badge = _badge(notes_count > 0)

    option_labels = {
        JobTab.OVERVIEW: JobTab.OVERVIEW.value,
        JobTab.RESUME: f"{JobTab.RESUME.value} {resume_badge}",
        JobTab.COVER: f"{JobTab.COVER.value} {cover_badge}",
        JobTab.RESPONSES: f"{JobTab.RESPONSES.value} {responses_badge}",
        JobTab.MESSAGES: f"{JobTab.MESSAGES.value} {messages_badge}",
        JobTab.NOTES: f"{JobTab.NOTES.value} {notes_badge}",
    }

    # Seed persisted tab selection
    if "job_tab_segmented" not in st.session_state:
        st.session_state["job_tab_segmented"] = JobTab.OVERVIEW

    selection = st.segmented_control(
        "Job tabs",
        options=list(option_labels.keys()),
        format_func=lambda tab: option_labels[tab],
        selection_mode="single",
        key="job_tab_segmented",
        label_visibility="collapsed",
        width="stretch",
    )

    if selection == JobTab.OVERVIEW:
        render_overview(job)  # type: ignore[arg-type]
    elif selection == JobTab.RESUME:
        render_resume(job)  # type: ignore[arg-type]
    elif selection == JobTab.COVER:
        render_cover(job)  # type: ignore[arg-type]
    elif selection == JobTab.RESPONSES:
        render_responses(job)  # type: ignore[arg-type]
    elif selection == JobTab.MESSAGES:
        render_messages(job)  # type: ignore[arg-type]
    elif selection == JobTab.NOTES:
        render_notes(job)  # type: ignore[arg-type]
    else:  # Fallback
        st.toast(f"Unknown tab: {selection}")
        render_overview(job)  # type: ignore[arg-type]


main()
