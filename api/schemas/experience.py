"""Pydantic schemas for Experience, Achievement, and Proposal models."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from src.database import ProposalStatus, ProposalType


class AchievementResponse(BaseModel):
    """Schema for achievement response."""

    id: int
    experience_id: int
    title: str
    content: str
    order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ExperienceCreate(BaseModel):
    """Schema for creating an experience."""

    company_name: str = Field(..., min_length=1, description="Company name")
    job_title: str = Field(..., min_length=1, description="Job title")
    location: str | None = Field(default=None, description="Job location")
    start_date: date = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: date | None = Field(default=None, description="End date (YYYY-MM-DD), null if current")
    company_overview: str | None = Field(default=None, description="Company overview")
    role_overview: str | None = Field(default=None, description="Role overview")
    skills: list[str] = Field(default_factory=list, description="List of skills")


class ExperienceUpdate(BaseModel):
    """Schema for updating an experience."""

    company_name: str | None = Field(default=None, min_length=1, description="Company name")
    job_title: str | None = Field(default=None, min_length=1, description="Job title")
    location: str | None = Field(default=None, description="Job location")
    start_date: date | None = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: date | None = Field(default=None, description="End date (YYYY-MM-DD), null if current")
    company_overview: str | None = Field(default=None, description="Company overview")
    role_overview: str | None = Field(default=None, description="Role overview")
    skills: list[str] | None = Field(default=None, description="List of skills")


class ExperienceResponse(BaseModel):
    """Schema for experience response."""

    id: int
    user_id: int
    company_name: str
    job_title: str
    location: str | None
    start_date: date
    end_date: date | None
    company_overview: str | None
    role_overview: str | None
    skills: list[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AchievementCreate(BaseModel):
    """Schema for creating an achievement."""

    title: str = Field(..., min_length=1, description="Achievement title")
    content: str = Field(..., min_length=1, description="Achievement content")
    order: int = Field(default=0, description="Order for sorting achievements")


class AchievementUpdate(BaseModel):
    """Schema for updating an achievement."""

    title: str | None = Field(default=None, min_length=1, description="Achievement title")
    content: str | None = Field(default=None, min_length=1, description="Achievement content")
    order: int | None = Field(default=None, description="Order for sorting achievements")


class ProposalResponse(BaseModel):
    """Schema for experience proposal response."""

    id: int
    session_id: int
    proposal_type: ProposalType
    experience_id: int
    achievement_id: int | None
    proposed_content: str  # JSON string
    original_proposed_content: str  # JSON string
    status: ProposalStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProposalCreate(BaseModel):
    """Schema for creating a proposal."""

    session_id: int = Field(..., description="Job intake session ID")
    proposal_type: ProposalType = Field(..., description="Type of proposal")
    experience_id: int = Field(..., description="Experience ID")
    achievement_id: int | None = Field(default=None, description="Achievement ID (for achievement proposals)")
    proposed_content: str = Field(..., description="JSON string containing proposal data")
    original_proposed_content: str = Field(..., description="JSON string of original proposal")
    status: ProposalStatus = Field(default=ProposalStatus.pending, description="Proposal status")


class ProposalUpdate(BaseModel):
    """Schema for updating a proposal."""

    proposed_content: str | None = Field(default=None, description="JSON string containing proposal data")
    status: ProposalStatus | None = Field(default=None, description="Proposal status")

