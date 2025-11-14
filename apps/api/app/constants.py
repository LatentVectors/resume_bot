"""Shared UI constants for the Streamlit app.

This module re-exports constants from src.constants for backward compatibility.
"""

from __future__ import annotations

# Re-export from src for backward compatibility
from src.constants import MIN_DATE, LLMTag

__all__ = ["LLMTag", "MIN_DATE"]
