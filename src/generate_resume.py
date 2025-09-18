"""LangGraph wrapper that returns structured ResumeData instead of a filename.

This module exposes a simple function, `generate_resume`, which runs the agent
graph and returns a `ResumeData` object. No file I/O is performed here.
"""

from __future__ import annotations

from typing import Any

from src.agents.main import InputState, OutputState, main_agent
from src.agents.main.state import Experience
from src.features.resume.types import ResumeData
from src.logging_config import logger


def generate_resume(
    job_description: str,
    experiences: list[Experience],
    responses: str,
    *,
    user_name: str,
    user_email: str,
    user_phone: str | None = None,
    user_linkedin_url: str | None = None,
    user_education: list[dict] | None = None,
) -> ResumeData:
    """Generate a ResumeData object using the agent graph.

    Args:
        job_description: The job description text used to tailor the resume.
        experiences: List of user experiences (internal model) for generation.
        responses: Free-form responses or notes captured in the app.
        user_name: User's full name.
        user_email: User's email address.
        user_phone: Optional phone number.
        user_linkedin_url: Optional LinkedIn profile URL.
        user_education: Optional list of education dicts from profile.

    Returns:
        ResumeData: Fully assembled resume data produced by the graph.
    """
    initial_state = InputState(
        job_description=job_description,
        experiences=experiences,
        responses=responses,
        user_name=user_name,
        user_email=user_email,
        user_phone=user_phone,
        user_linkedin_url=user_linkedin_url,
        user_education=user_education,
    )

    # Run the workflow
    result: Any = main_agent.invoke(initial_state)
    validated = OutputState.model_validate(result)

    if validated.resume_data is None:
        # This should not happen if the graph is correctly wired.
        logger.error("Agent returned no resume_data", exception=True)
        # Create a minimal empty structure to avoid consumer crashes.
        empty = ResumeData(
            name=user_name or "",
            title="",
            email=user_email or "",
            phone=user_phone or "",
            linkedin_url=user_linkedin_url or "",
            professional_summary="",
            experience=[],
            education=[],
            skills=[],
            certifications=[],
        )
        return empty

    # Smoke test: ensure ResumeData is serializable and matches schema
    json_payload = validated.resume_data.model_dump_json()
    round_tripped = ResumeData.model_validate_json(json_payload)

    logger.info("Workflow completed with assembled ResumeData")
    return round_tripped
