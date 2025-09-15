from __future__ import annotations

import streamlit as st

from .utils import SupportsJob


def render_messages(job: SupportsJob) -> None:  # noqa: ARG001 - placeholder
    """Render the Messages tab placeholder."""
    st.info("Messages linked to this job will be listed here.")
