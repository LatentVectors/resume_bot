from __future__ import annotations

import streamlit as st

from .utils import SupportsJob


def render_cover(job: SupportsJob) -> None:  # noqa: ARG001 - placeholder
    """Render the Cover Letter tab placeholder."""
    st.info("Cover letter content will appear here in a future sprint.")
