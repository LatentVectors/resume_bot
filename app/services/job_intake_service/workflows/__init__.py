"""Job intake workflows module."""

from __future__ import annotations

from app.services.job_intake_service.workflows.conversation_summary import summarize_conversation
from app.services.job_intake_service.workflows.experience_enhancement import (
    accept_achievement_update,
    accept_experience_update,
    accept_new_achievement,
    format_experiences_for_context,
    run_experience_chat,
)
from app.services.job_intake_service.workflows.gap_analysis import analyze_job_experience_fit
from app.services.job_intake_service.workflows.resume_generation import generate_resume_from_conversation
from app.services.job_intake_service.workflows.resume_refinement import run_resume_chat

__all__ = [
    # Experience enhancement
    "run_experience_chat",
    "accept_experience_update",
    "accept_achievement_update",
    "accept_new_achievement",
    "format_experiences_for_context",
    # Conversation summary
    "summarize_conversation",
    # Resume refinement
    "run_resume_chat",
    # Gap analysis
    "analyze_job_experience_fit",
    # Resume generation
    "generate_resume_from_conversation",
]
