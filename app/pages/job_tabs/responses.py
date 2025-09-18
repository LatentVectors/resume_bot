from __future__ import annotations

import streamlit as st

from src.database import Job as DbJob


def render_responses(job: DbJob) -> None:  # noqa: ARG001 - reserved for future use
    """Render the Responses tab placeholder."""
    st.info("Responses linked to this job will be listed here.")
