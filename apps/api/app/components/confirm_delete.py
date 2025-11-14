"""Shared delete confirmation component.

Provides a consistent confirmation UI with primary Delete and secondary Cancel.
"""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def confirm_delete(entity_label: str, on_confirm: Callable[[], None], on_cancel: Callable[[], None]) -> None:
    """Render a standardized delete confirmation UI.

    Args:
        entity_label: Human-friendly label of the entity to delete (e.g., "experience").
        on_confirm: Callback invoked when user confirms deletion.
        on_cancel: Callback invoked when user cancels.
    """
    st.warning(f"Are you sure you want to delete this {entity_label}?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Delete", type="primary", use_container_width=True):
            on_confirm()
    with col2:
        if st.button("Cancel", use_container_width=True):
            on_cancel()
