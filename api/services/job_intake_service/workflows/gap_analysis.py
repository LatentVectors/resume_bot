"""Gap analysis feature for matching job requirements to user experience.

This module provides functionality to analyze the fit between a job description
and a user's experience, identifying matched requirements, partial matches, gaps,
and suggesting clarifying questions.
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from openai import RateLimitError

from src.constants import LLMTag
from src.shared.formatters import format_experience_with_achievements
from src.core import ModelName, get_model
from src.core.prompts import PromptName, get_prompt
from src.core.prompts.input_types import GapAnalysisInput
from src.database import Experience, db_manager
from src.exceptions import OpenAIQuotaExceededError
from src.logging_config import logger


def analyze_job_experience_fit(job_description: str, experiences: list[Experience]) -> str:
    """Analyze how well user experiences match a job description.

    Uses an LLM to extract job requirements and match them against user experience,
    producing a structured report of matches, partial matches, gaps, and suggested
    questions for further clarification.

    Args:
        job_description: The full text of the job description to analyze
        experiences: List of user Experience objects to evaluate

    Returns:
        String containing matched requirements, partial matches, gaps,
        and suggested questions. On error, returns a report with has_error=True
        and empty lists.

    Raises:
        OpenAIQuotaExceededError: If OpenAI API quota is exceeded.
    """
    try:
        if not job_description or not job_description.strip():
            logger.warning("Gap analysis called with empty job description")
            return ""

        experience_summary = _format_experience_for_analysis(experiences)

        config = RunnableConfig(
            tags=[LLMTag.GAP_ANALYSIS.value],
        )

        inputs: GapAnalysisInput = {
            "job_description": job_description,
            "work_experience": experience_summary,
        }

        result = _chain.invoke(inputs, config=config)

        if not result or not result.strip():
            logger.warning("Gap analysis returned empty result from LLM")
            return ""

        return result

    except RateLimitError as exc:
        # Check if this is specifically a quota exceeded error
        error_message = str(exc)
        if "insufficient_quota" in error_message or "exceeded your current quota" in error_message:
            logger.error("OpenAI API quota exceeded during gap analysis: %s", exc)
            raise OpenAIQuotaExceededError() from exc
        # Re-raise other rate limit errors as generic exceptions
        logger.exception("OpenAI rate limit error during gap analysis: %s", exc)
        return ""
    except Exception as exc:
        # Broad catch to prevent errors from bubbling to UI
        logger.exception(
            "Gap analysis failed with exception. Job description length: %d, Experience count: %d, Error: %s",
            len(job_description) if job_description else 0,
            len(experiences),
            exc,
        )
        return ""


def _format_experience_for_analysis(experiences: list[Experience]) -> str:
    """Format experience records into a readable summary for the LLM.

    Args:
        experiences: List of Experience objects to format

    Returns:
        Formatted string summarizing the user's experience
    """
    if not experiences:
        return "No work experience provided."

    formatted_parts: list[str] = []

    for exp in experiences:
        # Fetch achievements for this experience
        achievements = db_manager.list_experience_achievements(exp.id)
        # Use the standardized formatter
        formatted = format_experience_with_achievements(exp, achievements)
        formatted_parts.append(formatted)

    return "\n\n".join(formatted_parts)


# Load prompt template and chain setup
_prompt = get_prompt(PromptName.GAP_ANALYSIS)
_llm = get_model(ModelName.OPENAI__GPT_4O)
_chain = _prompt | _llm | StrOutputParser()

