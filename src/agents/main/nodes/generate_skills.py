from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from openai import APIConnectionError
from pydantic import BaseModel, Field

from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

from ..state import InternalState, PartialInternalState
from .utils import format_experiences_for_prompt


def generate_skills(state: InternalState) -> PartialInternalState:
    """
    Generate a list of skills for a resume grounded in the user's experience and free-form responses to career-related questions, targeted for a specific job description.

    This node analyzes the job description, work experience, and additional responses to identify and extract relevant skills that the candidate possesses. The skills are generated using an LLM that matches the candidate's background with the requirements and preferences mentioned in the job description.

    Implementation Requirements:
    - Validate required inputs (job_description, experiences, responses) early
    - Use structured LLM output to ensure consistent format
    - Format experience data appropriately for the prompt
    - Return only the skills field in PartialInternalState
    - Handle LLM errors gracefully with retry logic
    - Log node execution for debugging
    - Generate 8-15 relevant skills that align with the job requirements

    Reads:
    - job_description: str - The target job description to extract relevant skills from
    - experiences: list[Experience] - List of work experience objects to analyze for skills
    - responses: str - Additional free-form responses that may contain skill information

    Returns:
    - skills: list[str] - Generated list of relevant skills for the resume
    """
    logger.debug("NODE: generate_skills")

    # Validate required inputs
    if not state.job_description:
        raise ValueError("job_description is required for skills generation")
    if not state.experiences:
        raise ValueError("experiences list cannot be empty for skills generation")

    # Format experiences for the prompt
    formatted_experiences = format_experiences_for_prompt(state.experiences)

    # Generate skills using LLM
    response = chain.invoke(
        {
            "job_description": state.job_description,
            "experiences": formatted_experiences,
            "responses": state.responses or "",
        }
    )

    validated = SkillsOutput.model_validate(response)
    return PartialInternalState(skills=validated.skills)


# Prompt templates
system_prompt = """
You are an expert resume writer specializing in identifying and extracting relevant skills from a candidate's background.

Your task is to analyze the job description, work experience, and additional information to generate a comprehensive list of skills that the candidate possesses and that are relevant to the target role.

Guidelines:
- Extract 8-15 skills that are most relevant to the job description
- Include both technical and soft skills
- Prioritize skills that are explicitly mentioned in the job description
- Include skills that can be inferred from the work experience
- Use industry-standard terminology for technical skills
- Include skills mentioned in the additional responses
- Avoid generic skills that don't add value
- Focus on skills that differentiate the candidate
"""

user_prompt = """
Job Description:
{job_description}

Candidate's Work Experience:
{experiences}

Additional Information:
{responses}

Generate a list of relevant skills that this candidate possesses and that align with the job requirements.
"""


# Pydantic model for structured output
class SkillsOutput(BaseModel):
    """Structured output for skills generation."""

    skills: list[str] = Field(
        description="A list of 8-15 relevant skills that the candidate possesses and that align with the job requirements. Include both technical and soft skills."
    )


# Model and chain setup
llm = get_model(OpenAIModels.gpt_4o_mini)
llm_structured = llm.with_structured_output(SkillsOutput).with_retry(retry_if_exception_type=(APIConnectionError,))
chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    | llm_structured
)
