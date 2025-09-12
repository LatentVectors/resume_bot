from __future__ import annotations

from datetime import date
from typing import TypedDict

from pydantic import BaseModel, Field


class Experience(BaseModel):
    """Experience model for resume generation."""

    id: str = Field(..., description="Unique identifier for the experience")
    company: str
    title: str
    start_date: date
    end_date: date | None = None
    content: str
    points: list[str] = Field(default_factory=list)

def create_experience(id: str, company: str, title: str, start_date: date, end_date: date | None, content: str, points: list[str]) -> Experience:
    """Create an experience object."""
    return Experience(
        id=id,
        company=company,
        title=title,
        start_date=start_date,
        end_date=end_date,
        content=content,
        points=points,
    )


class InputState(BaseModel):
    """Input state for resume generation agent."""

    job_description: str
    experiences: list[Experience]
    responses: str


class OutputState(BaseModel):
    """Output state for resume generation agent."""

    resume: str | None = None
    professional_summary: str | None = None
    skills: list[str] | None = None


class InternalState(InputState, OutputState, BaseModel):
    """Internal state for resume generation agent."""

    # All fields from InputState and OutputState are included
    # No additional internal fields needed for this agent


class PartialInternalState(TypedDict, total=False):
    """Partial internal state for node returns."""

    # InputState fields
    job_description: str
    experiences: list[Experience]
    responses: str

    # OutputState fields
    resume: str | None
    professional_summary: str | None
    skills: list[str] | None
