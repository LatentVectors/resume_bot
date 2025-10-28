"""Job intake service module."""

from __future__ import annotations

from app.services.job_intake_service.service import JobIntakeService
from app.services.job_intake_service.workflows import (
    analyze_job_experience_fit,
    generate_resume_from_conversation,
)

__all__ = [
    "JobIntakeService",
    # Gap analysis
    "analyze_job_experience_fit",
    # Resume generation
    "generate_resume_from_conversation",
]
