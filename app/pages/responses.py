from __future__ import annotations

from datetime import datetime

import streamlit as st

from app.services.user_service import UserService
from src.database import Response as DbResponse
from src.database import db_manager
from src.logging_config import logger
from src.utils.url import build_app_url


def _fmt_dt(dt: datetime | None) -> str:
    if not dt:
        return "—"
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return str(dt)


def main() -> None:
    st.title("🗂️ Responses")

    user = UserService.get_current_user()
    if not user:
        st.error("No user found. Please complete onboarding first.")
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
        responses: list[DbResponse] = db_manager.list_responses(sources=selected_sources, ignore=ignore_value)
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
            st.write(r.source)
        with row[2]:
            st.write((r.prompt[:120] + "…") if len(r.prompt) > 120 else r.prompt)
        with row[3]:
            st.write((r.response[:140] + "…") if len(r.response) > 140 else r.response)
        with row[4]:
            st.write("✅" if r.ignore else "—")
        with row[5]:
            if r.job_id:
                st.page_link(
                    build_app_url(f"/job?job_id={r.job_id}"),
                    label=f"View Job #{r.job_id}",
                    icon="🔗",
                    width="content",
                )
            else:
                st.write("—")


main()
