"""Pydantic schemas for Note model."""

from datetime import datetime

from pydantic import BaseModel, Field


class NoteResponse(BaseModel):
    """Schema for note response."""

    id: int
    job_id: int
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteCreate(BaseModel):
    """Schema for creating a note."""

    content: str = Field(..., min_length=1, description="Note content")


class NoteUpdate(BaseModel):
    """Schema for updating a note."""

    content: str = Field(..., min_length=1, description="Note content")

