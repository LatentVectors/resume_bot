"""Pydantic schemas for Cover Letter models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CoverLetterCreate(BaseModel):
    """Schema for creating a cover letter version."""

    cover_letter_json: str = Field(..., description="Cover letter JSON content")
    template_name: str = Field(default="cover_000.html", description="Template name")


class CoverLetterVersionResponse(BaseModel):
    """Schema for cover letter version response."""

    id: int
    cover_letter_id: int
    job_id: int
    version_index: int
    cover_letter_json: str
    template_name: str
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel


class CoverLetterResponse(BaseModel):
    """Schema for current cover letter response."""

    id: int
    job_id: int
    cover_letter_json: str
    template_name: str
    locked: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel


class CoverLetterPreviewRequest(BaseModel):
    """Schema for cover letter preview request."""

    cover_letter_data: dict[str, Any] = Field(..., description="Cover letter data as dict")
    template_name: str = Field(..., description="Template name")
