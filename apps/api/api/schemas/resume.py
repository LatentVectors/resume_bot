"""Pydantic schemas for Resume models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from src.database import ResumeVersionEvent


class ResumeCreate(BaseModel):
    """Schema for creating a resume version."""

    template_name: str = Field(..., description="Template name")
    resume_json: str = Field(..., description="Resume JSON content")
    event_type: ResumeVersionEvent = Field(default=ResumeVersionEvent.generate, description="Event type")
    parent_version_id: int | None = Field(default=None, description="Parent version ID for versioning")


class ResumeVersionResponse(BaseModel):
    """Schema for resume version response."""

    id: int
    job_id: int
    version_index: int
    parent_version_id: int | None
    event_type: ResumeVersionEvent
    template_name: str
    resume_json: str
    created_by_user_id: int
    created_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel


class ResumeResponse(BaseModel):
    """Schema for current resume response."""

    id: int
    job_id: int
    template_name: str
    resume_json: str
    pdf_filename: str | None
    locked: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel


class ResumePreviewRequest(BaseModel):
    """Schema for resume preview request."""

    resume_data: dict[str, Any] = Field(..., description="Resume data as dict")
    template_name: str = Field(..., description="Template name")


class ResumePreviewOverrideRequest(BaseModel):
    """Schema for resume preview with optional overrides."""

    resume_data: dict[str, Any] | None = Field(default=None, description="Resume data as dict (optional)")
    template_name: str | None = Field(default=None, description="Template name (optional)")


class ResumeCompareResponse(BaseModel):
    """Schema for resume comparison response."""

    version1: ResumeVersionResponse
    version2: ResumeVersionResponse
    diff: dict[str, Any] = Field(..., description="Comparison diff data")
