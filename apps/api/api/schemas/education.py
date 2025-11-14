"""Pydantic schemas for Education models."""

from datetime import date, datetime

from pydantic import BaseModel, Field


class EducationCreate(BaseModel):
    """Schema for creating an education entry."""

    institution: str = Field(..., min_length=1, description="Institution name")
    degree: str = Field(..., min_length=1, description="Degree type")
    major: str = Field(..., min_length=1, description="Major/field of study")
    grad_date: date = Field(..., description="Graduation date (YYYY-MM-DD)")


class EducationUpdate(BaseModel):
    """Schema for updating an education entry."""

    institution: str | None = Field(default=None, min_length=1, description="Institution name")
    degree: str | None = Field(default=None, min_length=1, description="Degree type")
    major: str | None = Field(default=None, min_length=1, description="Major/field of study")
    grad_date: date | None = Field(default=None, description="Graduation date (YYYY-MM-DD)")


class EducationResponse(BaseModel):
    """Schema for education response."""

    id: int
    user_id: int
    institution: str
    degree: str
    major: str
    grad_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel

