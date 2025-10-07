from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field, field_validator


class CoverLetterData(BaseModel):
    """Cover letter data structure."""

    name: str = Field(..., description="Full name")
    title: str = Field(..., description="Job title")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    date: dt.date = Field(..., description="Letter date")
    body_paragraphs: list[str] = Field(
        default_factory=list, min_length=0, max_length=4, description="Cover letter body paragraphs (0-4 paragraphs)"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email format validation."""
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v
