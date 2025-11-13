"""Pydantic schemas for Workflow request/response models."""

from datetime import date
from typing import Any

from pydantic import BaseModel, Field

from src.database import (
    AchievementAdd,
    AchievementUpdate,
    CompanyOverviewUpdate,
    RoleOverviewUpdate,
    SkillAdd,
)
from src.features.resume.types import ResumeData


# ==================== Gap Analysis ====================


class GapAnalysisRequest(BaseModel):
    """Schema for gap analysis request."""

    job_description: str = Field(..., min_length=1, description="Job description text")
    experience_ids: list[int] = Field(..., min_length=1, description="List of experience IDs to analyze")


class GapAnalysisResponse(BaseModel):
    """Schema for gap analysis response."""

    analysis: str = Field(..., description="Gap analysis markdown text")


# ==================== Stakeholder Analysis ====================


class StakeholderAnalysisRequest(BaseModel):
    """Schema for stakeholder analysis request."""

    job_description: str = Field(..., min_length=1, description="Job description text")
    experience_ids: list[int] = Field(..., min_length=1, description="List of experience IDs to analyze")


class StakeholderAnalysisResponse(BaseModel):
    """Schema for stakeholder analysis response."""

    analysis: str = Field(..., description="Stakeholder analysis markdown text")


# ==================== Experience Extraction ====================


class ExperienceExtractionRequest(BaseModel):
    """Schema for experience extraction request."""

    chat_messages: list[dict[str, Any]] = Field(
        ..., description="Chat message history as list of dicts with 'role' and 'content'"
    )
    experience_ids: list[int] = Field(..., min_length=1, description="List of experience IDs to analyze")


class WorkExperienceEnhancementSuggestions(BaseModel):
    """Schema for experience enhancement suggestions response."""

    role_overviews: list[RoleOverviewUpdate] = Field(
        default_factory=list, description="Suggestions for updating role overviews"
    )
    company_overviews: list[CompanyOverviewUpdate] = Field(
        default_factory=list, description="Suggestions for updating company overviews"
    )
    skills: list[SkillAdd] = Field(default_factory=list, description="Suggestions for adding new skills")
    achievements: list[AchievementAdd | AchievementUpdate] = Field(
        default_factory=list, description="Suggestions for adding or updating achievements"
    )


class ExperienceExtractionResponse(BaseModel):
    """Schema for experience extraction response."""

    suggestions: WorkExperienceEnhancementSuggestions = Field(
        ..., description="Structured suggestions for experience updates"
    )


# ==================== Resume Chat ====================


class ResumeChatMessage(BaseModel):
    """Schema for a chat message in resume chat."""

    role: str = Field(..., description="Message role: 'user', 'assistant', or 'tool'")
    content: str = Field(..., description="Message content")
    tool_call_id: str | None = Field(default=None, description="Tool call ID (for tool messages)")
    tool_calls: list[dict[str, Any]] | None = Field(default=None, description="Tool calls (for assistant messages)")


class ResumeChatRequest(BaseModel):
    """Schema for resume chat request."""

    messages: list[ResumeChatMessage] = Field(..., description="Chat message history")
    job_id: int = Field(..., description="Job ID")
    selected_version_id: int | None = Field(default=None, description="Selected resume version ID")
    gap_analysis: str = Field(..., description="Gap analysis markdown")
    stakeholder_analysis: str = Field(..., description="Stakeholder analysis markdown")
    work_experience: str = Field(..., description="Formatted work experience context")


class ResumeChatResponse(BaseModel):
    """Schema for resume chat response."""

    message: dict[str, Any] = Field(..., description="AI message response as dict")
    version_id: int | None = Field(default=None, description="New resume version ID if tool was used")


# ==================== Resume Generation ====================


class ResumeGenerationExperience(BaseModel):
    """Schema for experience in resume generation."""

    id: str = Field(..., description="Unique identifier for the experience")
    company: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    location: str = Field(default="", description="Job location")
    start_date: date = Field(..., description="Start date")
    end_date: date | None = Field(default=None, description="End date")
    content: str = Field(..., description="Experience content")
    points: list[str] = Field(default_factory=list, description="Bullet points")


class ResumeGenerationRequest(BaseModel):
    """Schema for resume generation request."""

    job_description: str = Field(..., min_length=1, description="Job description text")
    experiences: list[ResumeGenerationExperience] = Field(..., description="List of experiences")
    responses: str = Field(default="", description="Additional free-form responses")
    special_instructions: str | None = Field(default=None, description="Special instructions")
    resume_draft: ResumeData | None = Field(default=None, description="Current resume draft for grounding")


class ResumeGenerationResponse(BaseModel):
    """Schema for resume generation response."""

    resume_data: ResumeData = Field(..., description="Generated resume data")

