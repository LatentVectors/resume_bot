"""Shared UI constants for the Streamlit app."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

# Use a single application-wide minimum date for all date inputs
MIN_DATE: date = date(1950, 1, 1)


class LLMTag(StrEnum):
    JOB_EXTRACTION = "job_extraction"
    RESUME_GENERATION = "resume_generation"
