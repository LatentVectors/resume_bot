"""Pydantic models for structured output in agents."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


# ==================== Job Details Extraction Models ====================


class TitleCompany(BaseModel):
    """Structured output for job title and company extraction."""

    title: str | None = Field(default=None, description="The job title extracted from the text")
    company: str | None = Field(default=None, description="The company name extracted from the text")


# ==================== Resume Refinement Models ====================


class ProposedExperience(BaseModel):
    """Experience entry for AI-proposed resume draft.

    AI provides the experience ID (from database) along with refined title and bullet points.
    Company, location, and dates are pulled from the database automatically.
    """

    experience_id: int = Field(description="Database ID of the experience record")
    title: str = Field(description="Job title (can be refined from original)")
    points: list[str] = Field(description="List of bullet points describing achievements and responsibilities")


# ==================== Experience Enhancement Models ====================


class RoleOverviewUpdate(BaseModel):
    """Update suggestion for a role overview."""

    command: Literal["UPDATE"] = Field(default="UPDATE", description="The operation to perform")
    experience_id: int = Field(description="The unique identifier of the work experience entry to update")
    content: str = Field(description="The complete, new text for the role overview")


class CompanyOverviewUpdate(BaseModel):
    """Update suggestion for a company overview."""

    command: Literal["UPDATE"] = Field(default="UPDATE", description="The operation to perform")
    experience_id: int = Field(description="The unique identifier of the work experience entry to update")
    content: str = Field(description="The complete, new text for the company overview")


class SkillAdd(BaseModel):
    """Add suggestion for new skills."""

    command: Literal["ADD"] = Field(default="ADD", description="The operation to perform")
    experience_id: int = Field(description="The unique identifier of the work experience entry to add skills to")
    skills: list[str] = Field(description="A list of new, granular skills to add")


class AchievementAdd(BaseModel):
    """Add suggestion for a new achievement."""

    command: Literal["ADD"] = Field(default="ADD", description="The operation to perform")
    experience_id: int = Field(description="The unique identifier of the parent work experience")
    title: str = Field(description="The required title for the new achievement")
    content: str = Field(description="The full content of the new achievement")


class AchievementUpdate(BaseModel):
    """Update suggestion for an existing achievement."""

    command: Literal["UPDATE"] = Field(default="UPDATE", description="The operation to perform")
    experience_id: int = Field(description="The unique identifier of the parent work experience")
    achievement_id: int = Field(description="The required unique identifier of the achievement to update")
    title: str | None = Field(
        default=None, description="An optional new title. If null or omitted, the existing title is preserved"
    )
    content: str = Field(description="The complete, new text for the achievement's content")


class WorkExperienceEnhancementSuggestions(BaseModel):
    """Structured output schema for experience enhancement suggestions.

    Matches the schema defined in prompts/extract_experience_updates.json.
    """

    role_overviews: list[RoleOverviewUpdate] = Field(
        default_factory=list, description="A list of suggestions for updating role overviews"
    )
    company_overviews: list[CompanyOverviewUpdate] = Field(
        default_factory=list, description="A list of suggestions for updating company overviews"
    )
    skills: list[SkillAdd] = Field(default_factory=list, description="A list of suggestions for adding new skills")
    achievements: list[AchievementAdd | AchievementUpdate] = Field(
        default_factory=list, description="A list of suggestions for adding or updating achievements"
    )

