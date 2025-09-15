"""Jobs index with filters and status/favorite columns."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

import streamlit as st

from app.services.job_service import AllowedStatus, JobService
from app.services.user_service import UserService
from src.logging_config import logger
from src.utils.url import build_app_url

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


def _status_pill(status: AllowedStatus) -> str:
    # Colors per spec
    if status == "Saved":
        return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;background:#e5e7eb;color:#111827;font-size:12px;">Saved</span>'
    if status == "Applied":
        return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid #10b981;color:#065f46;background:#ffffff;font-size:12px;">Applied</span>'
    if status == "Interviewing":
        return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;background:#10b981;color:#ffffff;font-size:12px;">Interviewing</span>'
    if status == "Not Selected":
        return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;border:1px solid #ef4444;color:#991b1b;background:#ffffff;font-size:12px;">Not Selected</span>'
    if status == "No Offer":
        return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;background:#ef4444;color:#ffffff;font-size:12px;">No Offer</span>'
    # Hired
    return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;background:#10b981;color:#ffffff;font-size:12px;">Hired</span>'


def _format_dt(dt: object) -> str:
    if not dt:
        return "—"
    try:
        if isinstance(dt, datetime):
            return dt.strftime("%Y-%m-%d %H:%M:%S")
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
            st.markdown(_status_pill(job.status), unsafe_allow_html=True)  # type: ignore[arg-type]
        with cols[3]:
            st.write(_format_dt(getattr(job, "created_at", None)))
        with cols[4]:
            st.write(_format_dt(getattr(job, "applied_at", None)))
        with cols[5]:
            st.write("★" if getattr(job, "is_favorite", False) else "—")
        with cols[6]:
            st.write("✅" if getattr(job, "has_resume", False) else "—")
        with cols[7]:
            st.write("✅" if getattr(job, "has_cover_letter", False) else "—")
        with cols[8]:
            st.page_link(
                build_app_url(f"/job?job_id={job.id}"),
                label="View",
                icon="🔎",
            )


main()
