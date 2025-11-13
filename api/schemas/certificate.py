"""Pydantic schemas for Certificate models."""

from datetime import date as date_type
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


class CertificateCreate(BaseModel):
    """Schema for creating a certificate."""

    title: str = Field(..., min_length=1, description="Certificate title")
    institution: str | None = Field(default=None, description="Issuing institution")
    date: Annotated[date_type, Field(..., description="Certificate date (YYYY-MM-DD)")]


class CertificateUpdate(BaseModel):
    """Schema for updating a certificate."""

    title: str | None = Field(default=None, min_length=1, description="Certificate title")
    institution: str | None = Field(default=None, description="Issuing institution")
    date: Annotated[date_type | None, Field(default=None, description="Certificate date (YYYY-MM-DD)")]


class CertificateResponse(BaseModel):
    """Schema for certificate response."""

    id: int
    user_id: int
    title: str
    institution: str | None
    date: date_type
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel
