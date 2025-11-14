"""Pydantic schemas for User models."""

from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a user."""

    first_name: str = Field(..., min_length=1, description="User's first name")
    last_name: str = Field(..., min_length=1, description="User's last name")
    phone_number: str | None = Field(default=None, description="User's phone number")
    email: str | None = Field(default=None, description="User's email address")
    address: str | None = Field(default=None, description="User's street address")
    city: str | None = Field(default=None, description="User's city")
    state: str | None = Field(default=None, description="User's state")
    zip_code: str | None = Field(default=None, description="User's zip code")
    linkedin_url: str | None = Field(default=None, description="User's LinkedIn profile URL")
    github_url: str | None = Field(default=None, description="User's GitHub profile URL")
    website_url: str | None = Field(default=None, description="User's personal website URL")


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    first_name: str | None = Field(default=None, min_length=1, description="User's first name")
    last_name: str | None = Field(default=None, min_length=1, description="User's last name")
    phone_number: str | None = Field(default=None, description="User's phone number")
    email: str | None = Field(default=None, description="User's email address")
    address: str | None = Field(default=None, description="User's street address")
    city: str | None = Field(default=None, description="User's city")
    state: str | None = Field(default=None, description="User's state")
    zip_code: str | None = Field(default=None, description="User's zip code")
    linkedin_url: str | None = Field(default=None, description="User's LinkedIn profile URL")
    github_url: str | None = Field(default=None, description="User's GitHub profile URL")
    website_url: str | None = Field(default=None, description="User's personal website URL")


class UserResponse(BaseModel):
    """Schema for user response - used by both API and frontend."""

    id: int
    first_name: str
    last_name: str
    phone_number: str | None
    email: str | None
    address: str | None
    city: str | None
    state: str | None
    zip_code: str | None
    linkedin_url: str | None
    github_url: str | None
    website_url: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Allows conversion from SQLModel


class UserStatsResponse(BaseModel):
    """Schema for user statistics response."""

    jobs_applied_7_days: int = Field(default=0, description="Jobs applied in last 7 days")
    jobs_applied_30_days: int = Field(default=0, description="Jobs applied in last 30 days")
    total_jobs_saved: int = Field(default=0, description="Total jobs with status 'Saved'")
    total_jobs_applied: int = Field(default=0, description="Total jobs with status 'Applied' (all time)")
    total_interviews: int = Field(default=0, description="Total jobs with status 'Interviewing'")
    total_offers: int = Field(default=0, description="Total jobs with status 'Hired'")
    total_favorites: int = Field(default=0, description="Total favorite jobs")
    success_rate: float | None = Field(default=None, description="Success rate (offers / applications) as percentage")

