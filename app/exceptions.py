"""Custom exceptions for the application.

This module maintains backward compatibility by re-exporting exceptions from src.exceptions.
New code should import directly from src.exceptions.
"""

from __future__ import annotations

# Re-export for backward compatibility
from src.exceptions import OpenAIQuotaExceededError

__all__ = ["OpenAIQuotaExceededError"]
