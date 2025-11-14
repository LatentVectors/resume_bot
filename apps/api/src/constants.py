"""Shared constants used across the application."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

# Use a single application-wide minimum date for all date inputs
MIN_DATE: date = date(1950, 1, 1)


class LLMTag(StrEnum):
    """Tags for tracking LLM usage across different features."""

    JOB_EXTRACTION = "job_extraction"
    RESUME_GENERATION = "resume_generation"
    GAP_ANALYSIS = "gap_analysis"
    STAKEHOLDER_ANALYSIS = "stakeholder_analysis"
    INTAKE_SUMMARIZATION = "intake_summarization"
    INTAKE_EXPERIENCE_CHAT = "intake_experience_chat"
    INTAKE_RESUME_CHAT = "intake_resume_chat"
    EXPERIENCE_EXTRACTION = "experience_extraction"

