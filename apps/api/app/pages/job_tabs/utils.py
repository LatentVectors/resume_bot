from __future__ import annotations

from datetime import datetime

import streamlit as st


def fmt_datetime(dt: datetime | None) -> str:
    """Format a datetime for display.

    Args:
        dt: The datetime to format.

    Returns:
        A human-readable string representation or an em dash if missing.
    """
    if not dt:
        return "—"
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:  # pragma: no cover - defensive fallback
        return str(dt)


def fmt_date(dt: datetime | None) -> str:
    """Format a datetime for display as a date only (YYYY-MM-DD).

    Args:
        dt: The datetime to format.

    Returns:
        Date-only string or an em dash if missing.
    """
    if not dt:
        return "—"
    try:
        return dt.strftime("%Y-%m-%d")
    except Exception:  # pragma: no cover - defensive fallback
        return str(dt)


def badge(has_content: bool) -> str:
    """Return a Material icon token indicating content presence.

    Args:
        has_content: Whether the content exists.

    Returns:
        A Material icon token indicating content presence.
    """
    return ":material/check_circle:" if has_content else ":material/circle:"


def navigate_to_job(job_id: int) -> None:
    """Navigate to the Job detail page for the given job id.

    This sets session state keys and switches the page, resetting per-job state.

    Args:
        job_id: The job identifier to navigate to.
    """
    if not isinstance(job_id, int) or job_id <= 0:
        st.toast("Invalid job id", icon=":material/error_outline:")
        return

    # Only update if changed to avoid unnecessary reruns
    current = st.session_state.get("selected_job_id")
    if current != job_id:
        st.session_state["selected_job_id"] = job_id
        # Reset tab and any per-job temporary state
        st.session_state["selected_job_tab"] = "Overview"
        st.session_state.pop("resume_draft", None)
        st.session_state.pop("resume_template", None)
        st.session_state.pop("resume_instructions", None)

    st.switch_page("pages/job.py")
