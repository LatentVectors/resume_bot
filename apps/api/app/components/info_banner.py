"""Reusable UI components for Streamlit pages."""

from __future__ import annotations

import streamlit as st


def top_info_banner(
    message: str, *, button_label: str | None = None, target_page: str | None = None, key: str | None = None
) -> None:
    """Render an informational banner at the top with an optional navigation button.

    Args:
        message: Informational text to display.
        button_label: Optional label for a navigation button.
        target_page: Optional page path to navigate to when the button is clicked.
        key: Optional Streamlit key for the button to avoid collisions.
    """
    st.info(message)
    if button_label and target_page:
        if st.button(button_label, key=key, type="primary"):
            st.switch_page(target_page)
