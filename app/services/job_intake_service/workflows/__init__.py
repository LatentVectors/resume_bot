"""Job intake workflows module."""

from __future__ import annotations

from app.services.job_intake_service.workflows.gap_analysis import analyze_job_experience_fit
from app.services.job_intake_service.workflows.resume_generation import generate_resume_from_conversation
from app.services.job_intake_service.workflows.resume_refinement import run_resume_chat
from app.services.job_intake_service.workflows.stakeholder_analysis import analyze_stakeholders

__all__ = [
    # Resume refinement
    "run_resume_chat",
    # Gap analysis
    "analyze_job_experience_fit",
    # Stakeholder analysis
    "analyze_stakeholders",
    # Resume generation
    "generate_resume_from_conversation",
]
