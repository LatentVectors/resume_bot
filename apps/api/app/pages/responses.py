from __future__ import annotations

import asyncio
from datetime import datetime

import streamlit as st

from app.api_client.endpoints.responses import ResponsesAPI
from app.api_client.endpoints.users import UsersAPI
from app.pages.job_tabs.utils import navigate_to_job
from api.schemas.response import ResponseResponse
from src.logging_config import logger


def _fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(dt)


def main() -> None:
    st.title("Responses")

    try:
        user = asyncio.run(UsersAPI.get_current_user())
    except Exception as e:  # noqa: BLE001
        st.error("No user found. Please complete onboarding first.")
        logger.error(f"Error getting current user: {e}")
        return

    # Filters
    with st.container(border=True):
        st.subheader("Filters")
        col1, col2, col3 = st.columns([2, 2, 2])
        with col1:
            source_options = ["manual", "application"]
            selected_sources = st.multiselect(
                label="Source",
                options=source_options,
                default=source_options,
            )
        with col2:
            ignore_filter = st.selectbox(
                label="Ignored",
                options=["All", "Only Ignored", "Only Not Ignored"],
                index=0,
            )
        with col3:
            st.caption("Sorted by created date (newest first)")

    ignore_value: bool | None
    if ignore_filter == "Only Ignored":
        ignore_value = True
    elif ignore_filter == "Only Not Ignored":
        ignore_value = False
    else:
        ignore_value = None

    try:
        responses: list[ResponseResponse] = asyncio.run(
            ResponsesAPI.list_responses(sources=selected_sources if selected_sources else None, ignore=ignore_value)
        )
    except Exception as e:  # noqa: BLE001
        st.error("Failed to load responses. Please try again later.")
        logger.error(f"Error listing responses: {e}")
        return

    if not responses:
        st.info("No responses yet. You can create jobs from Home and generate content in future sprints.")
        return

    st.markdown("---")
    st.subheader("All Responses")

    # Header row
    header_cols = st.columns([1, 2, 3, 3, 1, 2])
    with header_cols[0]:
        st.markdown("**ID**")
    with header_cols[1]:
        st.markdown("**Source**")
    with header_cols[2]:
        st.markdown("**Prompt**")
    with header_cols[3]:
        st.markdown("**Response**")
    with header_cols[4]:
        st.markdown("**Ignored**")
    with header_cols[5]:
        st.markdown("**Job**")

    # Rows
    for r in responses:
        row = st.columns([1, 2, 3, 3, 1, 2])
        with row[0]:
            st.write(str(r.id))
        with row[1]:
            st.write(r.source.value if hasattr(r.source, "value") else str(r.source))
        with row[2]:
            st.write((r.prompt[:120] + "…") if len(r.prompt) > 120 else r.prompt)
        with row[3]:
            st.write((r.response[:140] + "…") if len(r.response) > 140 else r.response)
        with row[4]:
            st.write(":material/task_alt:" if r.ignore else "—")
        with row[5]:
            if r.job_id:
                if st.button(f"View Job #{r.job_id}", key=f"resp_view_job_{r.id}", icon=":material/link:"):
                    navigate_to_job(int(r.job_id))
            else:
                st.write("—")


main()
