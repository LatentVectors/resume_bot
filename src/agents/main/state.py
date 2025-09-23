from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import TypedDict

from pydantic import BaseModel, Field

from src.features.resume.types import ResumeData


class Experience(BaseModel):
    """Experience model for resume generation."""

    id: str = Field(..., description="Unique identifier for the experience")
    company: str
    title: str
    start_date: date
    end_date: date | None = None
    content: str
    points: list[str] = Field(default_factory=list)


def create_experience(
    id: str, company: str, title: str, start_date: date, end_date: date | None, content: str, points: list[str]
) -> Experience:
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
    special_instructions: str | None = None
    # Current resume draft object for grounding (stringified in prompts)
    resume_draft: ResumeData | None = None


class OutputState(BaseModel):
    """Output state for resume generation agent (public output)."""

    resume_data: ResumeData | None = None


class InternalState(InputState, OutputState, BaseModel):
    """Internal state for resume generation agent.

    Contains intermediate generated fields used to assemble the final
    resume_data, which is the only public output.
    """

    # Generated intermediate fields
    title: str | None = None
    professional_summary: str | None = None
    skills: list[str] | None = None

    # Router selections (which generator nodes to run next). If None or empty,
    # graph should default to running all generate nodes.
    router_targets: list[GenerateNode] | None = None


class PartialInternalState(TypedDict, total=False):
    """Partial internal state for node returns."""

    # InputState fields
    job_description: str
    experiences: list[Experience]
    responses: str
    special_instructions: str | None
    resume_draft: ResumeData | None

    # InternalState fields
    title: str | None
    professional_summary: str | None
    skills: list[str] | None

    # Router fields
    router_targets: list[GenerateNode] | None

    # OutputState fields
    resume_data: ResumeData | None


class GenerateNode(StrEnum):
    """Enum of generator nodes that the router can select."""

    skills = "skills"
    experience = "experience"
    professional_summary = "professional_summary"
