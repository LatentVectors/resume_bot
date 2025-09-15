from __future__ import annotations

import streamlit as st

from .utils import SupportsJob


def render_responses(job: SupportsJob) -> None:  # noqa: ARG001 - reserved for future use
    """Render the Responses tab placeholder."""
    st.info("Responses linked to this job will be listed here.")
