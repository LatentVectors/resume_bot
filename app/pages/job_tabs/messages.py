from __future__ import annotations

import streamlit as st

from src.database import Job as DbJob


def render_messages(job: DbJob) -> None:  # noqa: ARG001 - placeholder
    """Render the Messages tab placeholder."""
    st.info("Messages linked to this job will be listed here.")
