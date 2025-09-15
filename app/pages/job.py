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
from app.pages.job_tabs import (
    resume_exists as _resume_exists,
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
    # Query param handling
    qp = st.query_params
    job_id_param = qp.get("job_id")
    try:
        job_id = int(job_id_param) if job_id_param is not None else None
    except Exception:
        job_id = None

    if not job_id:
        st.error("Unknown or missing job_id. Return to Jobs.")
        st.page_link("pages/jobs.py", label="Back to Jobs", icon=":material/work:")
        return

    job = JobService.get_job(job_id)
    if not job:
        st.error("Job not found. It may have been removed.")
        st.page_link("pages/jobs.py", label="Back to Jobs", icon=":material/work:")
        return

    # Segmented control options with badges
    resp_count = JobService.count_job_responses(job.id)
    msg_count = JobService.count_job_messages(job.id)
    notes_count = JobService.count_job_notes(job.id)

    resume_badge = _badge(bool(job.has_resume or _resume_exists(getattr(job, "resume_filename", None))))
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

    selection = st.segmented_control(
        "",
        options=list(option_labels.keys()),
        format_func=lambda tab: option_labels[tab],
        selection_mode="single",
        default=JobTab.OVERVIEW,
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
