"""Pydantic schemas for Message models."""

from datetime import datetime

from pydantic import BaseModel, Field

from src.database import MessageChannel


class MessageCreate(BaseModel):
    """Schema for creating a message."""

    channel: MessageChannel = Field(..., description="Message channel")
    body: str = Field(..., min_length=1, description="Message body")


class MessageUpdate(BaseModel):
    """Schema for updating a message."""

    body: str | None = Field(default=None, min_length=1, description="Message body")
    sent_at: datetime | None = Field(default=None, description="Sent timestamp")


class MessageResponse(BaseModel):
    """Schema for message response."""

    id: int
    job_id: int
    channel: MessageChannel
    body: str
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime
    locked: bool  # Computed property from sent_at

    class Config:
        from_attributes = True  # Allows conversion from SQLModel

