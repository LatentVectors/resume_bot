"""Error handling utilities for the API."""

from __future__ import annotations

from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, id: int | str) -> None:
        """Initialize the exception.

        Args:
            resource: The type of resource that was not found (e.g., "Job", "User").
            id: The ID of the resource that was not found.
        """
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with id {id} not found",
        )


class ValidationError(HTTPException):
    """Raised when request validation fails."""

    def __init__(self, field_errors: dict[str, list[str]]) -> None:
        """Initialize the exception.

        Args:
            field_errors: Dictionary mapping field names to lists of error messages.
        """
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Validation error",
            headers={"X-Error-Code": "VALIDATION_ERROR"},
        )
        self.field_errors = field_errors


class QuotaExceededError(HTTPException):
    """Raised when OpenAI API quota is exceeded."""

    def __init__(self) -> None:
        """Initialize the exception."""
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="OpenAI API quota exceeded",
        )

