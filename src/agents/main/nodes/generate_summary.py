from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from openai import APIConnectionError
from pydantic import BaseModel, Field

from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

from ..state import InternalState, PartialInternalState
from .utils import format_experiences_for_prompt


def generate_summary(state: InternalState) -> PartialInternalState:
    """
    Generate a candidate title and professional summary grounded in the user's experience and
    free-form responses to career-related questions, targeted for a specific job description.

    This node creates a compelling professional summary and proposes a concise professional
    title that best positions the candidate for the target role. The LLM analyzes the job
    description, work experience, and additional responses to craft output tailored to the role.

    Implementation Requirements:
    - Validate required inputs (job_description, experiences, responses) early
    - Use structured LLM output to return both title and professional_summary
    - Format experience data appropriately for the prompt
    - Return only the title and professional_summary fields in PartialInternalState
    - Handle LLM errors gracefully with retry logic
    - Log node execution for debugging

    Reads:
    - job_description: str - The target job description to tailor the summary for
    - experiences: list[Experience] - List of work experience objects
    - responses: str - Additional free-form responses about career goals/background

    Returns:
    - title: str - Candidate professional title for the resume header
    - professional_summary: str - Generated professional summary text
    """
    logger.debug("NODE: generate_summary")

    # Validate required inputs
    if not state.job_description:
        raise ValueError("job_description is required for summary generation")
    if not state.experiences:
        raise ValueError("experiences list cannot be empty for summary generation")

    # Format experiences for the prompt
    formatted_experiences = format_experiences_for_prompt(state.experiences)

    # Generate title and summary using LLM (structured output)
    response = chain.invoke(
        {
            "job_description": state.job_description,
            "experiences": formatted_experiences,
            "responses": state.responses or "",
        }
    )

    validated = SummaryOutput.model_validate(response)

    return PartialInternalState(title=validated.title, professional_summary=validated.professional_summary)


# Prompt templates
system_prompt = """
You are an expert resume writer. Produce BOTH a concise professional TITLE and a compelling
PROFESSIONAL SUMMARY tailored to the target job.

Guidelines (Title):
- 2-5 words, concise and role-aligned (e.g., "Senior Data Scientist")
- Reflect candidate's seniority and expertise relative to the job description
- Avoid company-specific or overly generic titles (e.g., not just "Engineer")

Guidelines (Professional Summary):
- 3-4 sentences, roughly 50-90 words
- Highlight the most relevant experience, impact, and skills for the role
- Use action verbs and quantifiable achievements when possible
- Match tone and keywords from the job description
- Avoid clichés and fluff; be specific and value-focused
"""

user_prompt = """
Job Description:
{job_description}

Candidate's Work Experience:
{experiences}

Additional Information:
{responses}

Produce a JSON object with fields:
  - title: string (concise, role-aligned professional title)
  - professional_summary: string (3-4 sentences tailored to the role)
"""


class SummaryOutput(BaseModel):
    """Structured output for title and professional summary generation."""

    title: str = Field(description="Concise professional title for the resume header")
    professional_summary: str = Field(description="3-4 sentence professional summary tailored to the role")


# Model and chain setup
llm = get_model(OpenAIModels.gpt_4o_mini)
llm_structured = llm.with_structured_output(SummaryOutput).with_retry(retry_if_exception_type=(APIConnectionError,))
chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    | llm_structured
)
