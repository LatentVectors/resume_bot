"""LangGraph workflow for resume generation."""

from src.agents.main import InputState, OutputState, main_agent
from src.agents.main.state import Experience
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
) -> str:
    """Generate a resume using the workflow."""
    # Create initial state
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
    result = main_agent.invoke(initial_state)
    validated = OutputState.model_validate(result)

    logger.info(f"Workflow completed with response: {validated.resume}")
    return validated.resume
