"""Pydantic schemas for Job models."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.database import JobStatus


class JobCreate(BaseModel):
    """Schema for creating a job."""

    title: str | None = Field(default=None, description="Job title")
    company: str | None = Field(default=None, description="Company name")
    description: str = Field(..., min_length=1, description="Job description")
    favorite: bool = Field(default=False, description="Mark as favorite")
    status: JobStatus | None = Field(default=None, description="Job status")


class JobUpdate(BaseModel):
    """Schema for updating a job."""

    title: str | None = Field(default=None, description="Job title")
    company: str | None = Field(default=None, description="Company name")
    description: str | None = Field(default=None, min_length=1, description="Job description")
    favorite: bool | None = Field(default=None, description="Mark as favorite")
    status: JobStatus | None = Field(default=None, description="Job status")


class JobResponse(BaseModel):
    """Schema for job response - used by both API and frontend."""

    id: int
    user_id: int
    job_title: str | None
    company_name: str | None
    job_description: str
    is_favorite: bool
    status: JobStatus
    has_resume: bool
    has_cover_letter: bool
    created_at: datetime
    updated_at: datetime
    applied_at: datetime | None = None

    class Config:
        from_attributes = True  # Allows conversion from SQLModel

