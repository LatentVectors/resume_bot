"""Pydantic schemas for Response models."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.database import ResponseSource


class ResponseCreate(BaseModel):
    """Schema for creating a response."""

    job_id: int | None = Field(default=None, description="Associated job ID")
    prompt: str = Field(..., min_length=1, description="Prompt/question")
    response: str = Field(..., min_length=1, description="Response text")
    source: ResponseSource = Field(..., description="Response source")
    ignore: bool = Field(default=False, description="Ignore flag")


class ResponseUpdate(BaseModel):
    """Schema for updating a response."""

    prompt: str | None = Field(default=None, min_length=1, description="Prompt/question")
    response: str | None = Field(default=None, min_length=1, description="Response text")
    ignore: bool | None = Field(default=None, description="Ignore flag")
    locked: bool | None = Field(default=None, description="Locked flag")


class ResponseResponse(BaseModel):
    """Schema for response response."""

    id: int
    job_id: int | None
    prompt: str
    response: str
    source: ResponseSource
    ignore: bool
    locked: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel

