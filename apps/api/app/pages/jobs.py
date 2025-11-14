"""Jobs index with filters and status/favorite columns."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime

import streamlit as st

from api.schemas.job import JobResponse
from app.api_client.endpoints.jobs import JobsAPI
from app.api_client.endpoints.users import UsersAPI
from app.components.confirm_delete import confirm_delete
from app.components.status_badge import render_status_badge
from app.pages.job_tabs.utils import navigate_to_job
from src.database import JobStatus
from src.logging_config import logger

AllowedStatuses: tuple[str, ...] = (
    "Saved",
    "Applied",
    "Interviewing",
    "Not Selected",
    "No Offer",
    "Hired",
)

AllowedStatus = str  # Type alias for compatibility


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
    try:
        user = asyncio.run(UsersAPI.get_current_user())
    except Exception as e:
        st.error(f"Error loading user: {str(e)}")
        logger.error(f"Error loading current user: {e}")
        return

    if not user:
        st.error("No user found. Please complete onboarding first.")
        return

    # Initialize session state for job selection
    if "selected_job_ids" not in st.session_state:
        st.session_state.selected_job_ids = set()
    if "show_delete_confirmation" not in st.session_state:
        st.session_state.show_delete_confirmation = False

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

    # Query jobs via API - need to handle multiple statuses
    # Since API only accepts single status_filter, make multiple calls and combine
    try:
        all_jobs: list[JobResponse] = []
        seen_job_ids: set[int] = set()

        # If no statuses selected, use default statuses
        statuses_to_query = statuses_widget or default_statuses

        # Make API call for each status and combine results (deduplicate by ID)
        for status_str in statuses_to_query:
            try:
                # Convert string status to JobStatus enum
                status_enum = JobStatus(status_str)
                status_jobs = asyncio.run(
                    JobsAPI.list_jobs(
                        user_id=user.id,
                        status_filter=status_enum,
                        favorite_only=favorites_widget,
                    )
                )
                # Add jobs that haven't been seen yet
                for job in status_jobs:
                    if job.id not in seen_job_ids:
                        all_jobs.append(job)
                        seen_job_ids.add(job.id)
            except ValueError:
                # Invalid status, skip
                logger.warning(f"Invalid status: {status_str}")
                continue

        # Sort by created_at descending (most recent first)
        jobs = sorted(all_jobs, key=lambda j: j.created_at, reverse=True)
    except Exception as e:  # noqa: BLE001
        st.error("Failed to load jobs. Please try again later.")
        logger.exception("Error listing jobs for user %s: %s", user.id, e)
        return

    if not jobs:
        st.info("No jobs match the current filters.")
        return

    st.markdown("---")

    # Bulk actions bar
    if st.session_state.selected_job_ids:
        col1, col2, col3 = st.columns([1, 2, 9])
        with col1:
            if st.button("Clear Selection", use_container_width=True):
                st.session_state.selected_job_ids = set()
                st.rerun()
        with col2:
            if st.button(
                f"Delete {len(st.session_state.selected_job_ids)} job(s)",
                type="primary",
                use_container_width=True,
            ):
                st.session_state.show_delete_confirmation = True
                st.rerun()
        with col3:
            st.markdown(f"**{len(st.session_state.selected_job_ids)} job(s) selected**")

    # Show confirmation modal
    if st.session_state.show_delete_confirmation:

        @st.dialog("Confirm Deletion", width="small")
        def confirm_deletion_modal() -> None:
            job_count = len(st.session_state.selected_job_ids)
            entity_label = f"{job_count} job(s)" if job_count > 1 else "job"

            def on_confirm() -> None:
                try:
                    job_ids_to_delete = list(st.session_state.selected_job_ids)
                    successful = 0
                    failed = 0

                    # Delete each job individually via API
                    for job_id in job_ids_to_delete:
                        try:
                            asyncio.run(JobsAPI.delete_job(job_id))
                            successful += 1
                        except Exception as e:  # noqa: BLE001
                            logger.error(f"Failed to delete job {job_id}: {e}")
                            failed += 1

                    if failed > 0:
                        st.error(f"Deleted {successful} job(s), but {failed} failed to delete.")
                    else:
                        st.success(f"Successfully deleted {successful} job(s).")

                    st.session_state.selected_job_ids = set()
                    st.session_state.show_delete_confirmation = False
                    st.rerun()
                except Exception as e:  # noqa: BLE001
                    logger.exception("Error during bulk delete: %s", e)
                    st.error("Failed to delete jobs. Please try again.")

            def on_cancel() -> None:
                st.session_state.show_delete_confirmation = False
                st.rerun()

            confirm_delete(entity_label, on_confirm, on_cancel)

        confirm_deletion_modal()

    st.subheader("Job Applications")

    # Get all job IDs for select all functionality
    all_job_ids = {int(job.id) for job in jobs if job.id}

    # Header row with checkbox: Select | Title | Company | Status | Created | Applied | Favorite | Resume | Cover Letter | View
    header_cols = st.columns([0.5, 3, 3, 2, 2, 2, 1.5, 1.5, 2, 1.5])
    with header_cols[0]:
        all_selected = all_job_ids.issubset(st.session_state.selected_job_ids) if all_job_ids else False
        select_all = st.checkbox(
            "Select all",
            value=all_selected,
            key="select_all_jobs",
            label_visibility="collapsed",
        )
        if select_all and not all_selected:
            st.session_state.selected_job_ids.update(all_job_ids)
            st.rerun()
        elif not select_all and all_selected:
            st.session_state.selected_job_ids -= all_job_ids
            st.rerun()
    with header_cols[1]:
        st.markdown("**Title**")
    with header_cols[2]:
        st.markdown("**Company**")
    with header_cols[3]:
        st.markdown("**Status**")
    with header_cols[4]:
        st.markdown("**Created**")
    with header_cols[5]:
        st.markdown("**Applied**")
    with header_cols[6]:
        st.markdown("**Favorite**")
    with header_cols[7]:
        st.markdown("**Resume**")
    with header_cols[8]:
        st.markdown("**Cover Letter**")
    with header_cols[9]:
        st.markdown("**View**")

    for job in jobs:
        job_id = int(job.id) if job.id else 0
        cols = st.columns([0.5, 3, 3, 2, 2, 2, 1.5, 1.5, 2, 1.5])

        with cols[0]:
            is_selected = job_id in st.session_state.selected_job_ids
            selected = st.checkbox(
                f"Select job {job_id}",
                value=is_selected,
                key=f"select_job_{job_id}",
                label_visibility="collapsed",
            )
            if selected and not is_selected:
                st.session_state.selected_job_ids.add(job_id)
                st.rerun()
            elif not selected and is_selected:
                st.session_state.selected_job_ids.discard(job_id)
                st.rerun()

        with cols[1]:
            st.write(job.job_title or "—")
        with cols[2]:
            st.write(job.company_name or "—")
        with cols[3]:
            _status_badge(job.status)
        with cols[4]:
            st.write(_format_dt(job.created_at))
        with cols[5]:
            st.write(_format_dt(job.applied_at))
        with cols[6]:
            st.write(":material/star:" if job.is_favorite else "—")
        with cols[7]:
            st.write(":material/task_alt:" if job.has_resume else "—")
        with cols[8]:
            st.write(":material/task_alt:" if job.has_cover_letter else "—")
        with cols[9]:
            if st.button("", key=f"view_job_{job.id}", icon=":material/visibility:", help="View job"):
                navigate_to_job(int(job.id))


main()
