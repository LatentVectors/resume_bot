from __future__ import annotations

import streamlit as st

from src.database import Job as DbJob


def render_cover(job: DbJob) -> None:  # noqa: ARG001 - placeholder
    """Render the Cover Letter tab placeholder."""
    st.info("Cover letter content will appear here in a future sprint.")
