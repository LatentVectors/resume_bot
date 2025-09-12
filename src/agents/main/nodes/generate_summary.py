from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate
from openai import APIConnectionError

from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

from ..state import InternalState, PartialInternalState
from .utils import format_experiences_for_prompt


def generate_summary(state: InternalState) -> PartialInternalState:
    """
    Generate a professional summary grounded in the user's experience and free-form responses to career-related questions, targeted for a specific job description.

    This node creates a compelling professional summary that highlights the candidate's most relevant experience and skills as they relate to the target job. The summary is generated using an LLM that analyzes the job description, work experience, and additional responses to craft a personalized, impactful summary.

    Implementation Requirements:
    - Validate required inputs (job_description, experiences, responses) early
    - Use string parser for free-form text output
    - Format experience data appropriately for the prompt
    - Return only the professional_summary field in PartialInternalState
    - Handle LLM errors gracefully with retry logic
    - Log node execution for debugging

    Reads:
    - job_description: str - The target job description to tailor the summary for
    - experiences: list[Experience] - List of work experience objects
    - responses: str - Additional free-form responses about career goals/background

    Returns:
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

    # Generate summary using LLM
    response = chain.invoke(
        {
            "job_description": state.job_description,
            "experiences": formatted_experiences,
            "responses": state.responses or "",
        }
    )

    return PartialInternalState(professional_summary=response)


# Prompt templates
system_prompt = """
You are an expert resume writer specializing in creating compelling professional summaries.
Your task is to write a professional summary that effectively markets the candidate for the specific job they're applying to.

Guidelines:
- Keep the summary concise (3-4 sentences, 50-75 words)
- Highlight the most relevant experience and skills for the target role
- Use strong action words and quantifiable achievements when possible
- Tailor the language to match the job description's tone and requirements
- Focus on value proposition and career progression
- Avoid generic phrases and clichés
"""

user_prompt = """
Job Description:
{job_description}

Candidate's Work Experience:
{experiences}

Additional Information:
{responses}

Write a professional summary that positions this candidate as an ideal fit for the role.
"""

# Model and chain setup
llm = get_model(OpenAIModels.gpt_4o_mini)
llm_with_retry = llm.with_retry(retry_if_exception_type=(APIConnectionError,))
chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    | llm_with_retry
    | StrOutputParser()
)
