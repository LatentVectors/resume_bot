"""Shared exceptions for the application."""

from __future__ import annotations


class OpenAIQuotaExceededError(Exception):
    """Raised when OpenAI API quota is exceeded (429 error with insufficient_quota)."""

    def __init__(self, message: str = "OpenAI API quota exceeded. Please add credits to your account.") -> None:
        """Initialize the exception.

        Args:
            message: Error message to display.
        """
        self.message = message
        super().__init__(self.message)

