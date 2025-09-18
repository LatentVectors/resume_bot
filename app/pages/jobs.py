"""Jobs index with filters and status/favorite columns."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import streamlit as st

from app.components.status_badge import render_status_badge
from app.pages.job_tabs.utils import navigate_to_job
from app.services.job_service import AllowedStatus, JobService
from app.services.user_service import UserService
from src.logging_config import logger

AllowedStatuses: tuple[AllowedStatus, ...] = (
    "Saved",
    "Applied",
    "Interviewing",
    "Not Selected",
    "No Offer",
    "Hired",
)


def _parse_status_params(value: object) -> list[AllowedStatus]:
    if value is None:
        return []
    # Streamlit may return str or list[str]
    try:
        if isinstance(value, str):
            raw = [v.strip() for v in value.split(",") if v.strip()]
        elif isinstance(value, Sequence):
            raw = []
            for item in value:  # type: ignore[assignment]
                if isinstance(item, str):
                    raw.extend([v.strip() for v in item.split(",") if v.strip()])
        else:
            raw = []
    except Exception:
        raw = []

    result: list[AllowedStatus] = []
    for v in raw:
        if v in AllowedStatuses:
            result.append(v)  # type: ignore[arg-type]
    return result


def _bool_param(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = str(value).lower().strip()
    return s in ("1", "true", "yes", "on")


def _normalize_status_label(status: object) -> AllowedStatus:
    """Return a user-facing status label from a string or Enum-like value."""
    # Raw string from enum.value or fallback to str(status)
    raw: str
    if isinstance(status, str):
        raw = status
    else:
        val = getattr(status, "value", None)
        raw = val if isinstance(val, str) else str(status)

    raw = raw.strip()

    # Direct match to allowed labels
    if raw in AllowedStatuses:
        return raw  # type: ignore[return-value]

    # Handle forms like "JobStatus.Saved" or enum names without spaces
    if "." in raw:
        raw = raw.split(".")[-1]

    name_to_label: dict[str, AllowedStatus] = {
        "Saved": "Saved",
        "Applied": "Applied",
        "Interviewing": "Interviewing",
        "NotSelected": "Not Selected",
        "NoOffer": "No Offer",
        "Hired": "Hired",
    }
    label = name_to_label.get(raw)
    if label:
        return label

    # Fallback
    return "Saved"  # type: ignore[return-value]


def _status_badge(status: object) -> None:
    render_status_badge(status)


def _format_dt(dt: object) -> str:
    if not dt:
        return "—"
    try:
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d")
        return str(dt)
    except Exception:
        return str(dt)


def main() -> None:
    user = UserService.get_current_user()
    if not user:
        st.error("No user found. Please complete onboarding first.")
        return

    # Read query params and establish defaults
    qp = st.query_params
    default_statuses: list[AllowedStatus] = ["Saved", "Applied", "Interviewing"]
    selected_statuses = _parse_status_params(qp.get("status")) or default_statuses
    favorites_only = _bool_param(qp.get("fav"), default=False)

    st.markdown("---")
    st.subheader("Filters")
    fcol1, fcol2, fcol3 = st.columns([3, 1, 1])
    with fcol1:
        statuses_widget = st.multiselect(
            label="Status",
            options=list(AllowedStatuses),
            default=selected_statuses,
            placeholder="Select statuses...",
            key="jobs_filter_statuses",
        )
    with fcol2:
        favorites_widget = st.toggle("Favorites only", value=favorites_only, key="jobs_filter_fav")
    with fcol3:
        if st.button("Reset", use_container_width=True):
            st.query_params.clear()
            st.rerun()

    # Persist filters in query params when changed
    changed = False
    if set(statuses_widget) != set(selected_statuses):
        if statuses_widget:
            st.query_params["status"] = ",".join(statuses_widget)
        else:
            # If none selected, drop param so defaults apply
            st.query_params.pop("status", None)
        changed = True
    if bool(favorites_widget) != bool(favorites_only):
        if favorites_widget:
            st.query_params["fav"] = "1"
        else:
            st.query_params.pop("fav", None)
        changed = True
    if changed:
        st.rerun()

    # Query jobs via service with default sort by created desc
    try:
        jobs = JobService.list_jobs(user.id, statuses_widget or default_statuses, favorites_widget)
    except Exception as e:  # noqa: BLE001
        st.error("Failed to load jobs. Please try again later.")
        logger.exception("Error listing jobs for user %s: %s", user.id, e)
        return

    if not jobs:
        st.info("No jobs match the current filters.")
        return

    st.markdown("---")
    st.subheader("Job Applications")

    # Header row: Title | Company | Status | Created | Applied | Favorite | Resume | Cover Letter | View
    header_cols = st.columns([3, 3, 2, 2, 2, 1.5, 1.5, 2, 1.5])
    with header_cols[0]:
        st.markdown("**Title**")
    with header_cols[1]:
        st.markdown("**Company**")
    with header_cols[2]:
        st.markdown("**Status**")
    with header_cols[3]:
        st.markdown("**Created**")
    with header_cols[4]:
        st.markdown("**Applied**")
    with header_cols[5]:
        st.markdown("**Favorite**")
    with header_cols[6]:
        st.markdown("**Resume**")
    with header_cols[7]:
        st.markdown("**Cover Letter**")
    with header_cols[8]:
        st.markdown("**View**")

    for job in jobs:
        cols = st.columns([3, 3, 2, 2, 2, 1.5, 1.5, 2, 1.5])
        with cols[0]:
            st.write(job.job_title or "—")
        with cols[1]:
            st.write(job.company_name or "—")
        with cols[2]:
            _status_badge(job.status)
        with cols[3]:
            st.write(_format_dt(job.created_at))
        with cols[4]:
            st.write(_format_dt(job.applied_at))
        with cols[5]:
            st.write(":material/star:" if job.is_favorite else "—")
        with cols[6]:
            st.write(":material/task_alt:" if job.has_resume else "—")
        with cols[7]:
            st.write(":material/task_alt:" if job.has_cover_letter else "—")
        with cols[8]:
            if st.button("", key=f"view_job_{job.id}", icon=":material/visibility:", help="View job"):
                navigate_to_job(int(job.id))


main()
