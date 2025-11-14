"""Shared formatting utilities for displaying data.

This module re-exports formatters from src.shared.formatters for backward compatibility.
"""

from __future__ import annotations

# Re-export from src for backward compatibility
from src.shared.formatters import (
    format_all_experiences,
    format_experience_with_achievements,
)

__all__ = ["format_experience_with_achievements", "format_all_experiences"]
