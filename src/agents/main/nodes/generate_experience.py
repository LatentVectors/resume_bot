from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from openai import APIConnectionError
from pydantic import BaseModel, Field

from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

from ..state import Experience, InternalState, PartialInternalState
from .utils import format_experiences_for_prompt


def generate_experience(state: InternalState) -> PartialInternalState:
    """
    Generate experience bullet points for a resume grounded in the user's experience and free-form responses to career-related questions, targeted for a specific job description.

    This node analyzes each work experience and generates compelling, job-specific bullet points that highlight achievements and responsibilities relevant to the target role. The LLM uses structured output to match generated bullet points to specific experience objects using their IDs, ensuring accurate attribution and allowing for targeted improvements.

    Implementation Requirements:
    - Validate required inputs (job_description, experiences, responses) early
    - Use structured LLM output to match bullet points to experience IDs
    - Format experience data appropriately for the prompt
    - Merge generated bullet points into existing experience objects
    - Return only the experiences field in PartialInternalState
    - Handle LLM errors gracefully with retry logic
    - Log node execution for debugging
    - Generate 3-5 bullet points per experience that are relevant to the job

    Reads:
    - job_description: str - The target job description to tailor bullet points for
    - experiences: list[Experience] - List of work experience objects to enhance
    - responses: str - Additional free-form responses that may contain relevant context

    Returns:
    - experiences: list[Experience] - Updated experience objects with enhanced bullet points
    """
    logger.debug("NODE: generate_experience")

    # Validate required inputs
    if not state.job_description:
        raise ValueError("job_description is required for experience generation")
    if not state.experiences:
        raise ValueError("experiences list cannot be empty for experience generation")

    # Format experiences for the prompt
    formatted_experiences = format_experiences_for_prompt(state.experiences)

    # Generate enhanced bullet points using LLM
    response = chain.invoke(
        {
            "job_description": state.job_description,
            "experiences": formatted_experiences,
            "responses": state.responses or "",
        }
    )

    validated = ExperienceOutput.model_validate(response)

    # Create a mapping of experience ID to experience object
    experience_map = {exp.id: exp for exp in state.experiences}

    # Update experiences with generated bullet points
    updated_experiences = []
    for exp_id, exp in experience_map.items():
        # Find bullet points for this experience
        experience_bullets = [
            bullet.bullet_point for bullet in validated.bullet_points if bullet.experience_id == exp_id
        ]

        # Create updated experience with new bullet points
        updated_exp = Experience(
            id=exp.id,
            company=exp.company,
            title=exp.title,
            start_date=exp.start_date,
            end_date=exp.end_date,
            content=exp.content,
            points=experience_bullets if experience_bullets else exp.points,
        )
        updated_experiences.append(updated_exp)

    return PartialInternalState(experiences=updated_experiences)


# Prompt templates
system_prompt = """
You are an expert resume writer specializing in creating compelling, achievement-focused bullet points for work experience.

Your task is to analyze each work experience and generate 3-5 impactful bullet points that highlight the candidate's achievements and responsibilities in a way that's relevant to the target job.

Guidelines:
- Generate 3-5 bullet points per experience
- Use strong action verbs and quantifiable achievements when possible
- Tailor bullet points to match the job description's requirements
- Focus on results and impact rather than just responsibilities
- Use industry-standard terminology
- Make bullet points specific and concrete
- Avoid generic or vague statements
- Each bullet point should be 1-2 lines maximum
- Prioritize achievements that align with the target role
"""

user_prompt = """
Job Description:
{job_description}

Candidate's Work Experience:
{experiences}

Additional Information:
{responses}

For each work experience, generate 3-5 compelling bullet points that highlight achievements and responsibilities relevant to the target role. Match each bullet point to the specific experience using the experience ID.
"""


# Pydantic models for structured output
class BulletPoint(BaseModel):
    """Individual bullet point with experience ID mapping."""

    experience_id: str = Field(description="ID of the experience this bullet point belongs to")
    bullet_point: str = Field(description="The bullet point text (1-2 lines, achievement-focused)")


class ExperienceOutput(BaseModel):
    """Structured output for experience bullet point generation."""

    bullet_points: list[BulletPoint] = Field(
        description="List of bullet points, each mapped to a specific experience ID"
    )


# Model and chain setup
llm = get_model(OpenAIModels.gpt_4o_mini)
llm_structured = llm.with_structured_output(ExperienceOutput).with_retry(retry_if_exception_type=(APIConnectionError,))
chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    | llm_structured
)
