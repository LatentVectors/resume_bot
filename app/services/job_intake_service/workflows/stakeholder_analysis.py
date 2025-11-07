"""Stakeholder analysis feature for understanding hiring manager perspectives.

This module provides functionality to analyze who the hiring stakeholders are,
what they're looking for, and how they may perceive the candidate's background.
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableConfig
from openai import RateLimitError

from app.constants import LLMTag
from app.exceptions import OpenAIQuotaExceededError
from app.shared.formatters import format_experience_with_achievements
from src.core.models import OpenAIModels, get_model
from src.core.prompts import PromptName, get_prompt
from src.core.prompts.input_types import StakeholderAnalysisInput
from src.database import Experience, db_manager
from src.logging_config import logger


def analyze_stakeholders(job_description: str, experiences: list[Experience]) -> str:
    """Analyze hiring stakeholders and their likely perceptions of the candidate.

    Uses an LLM to identify key hiring stakeholders, their priorities, and how
    they may perceive the candidate's background based on their experience.

    Args:
        job_description: The full text of the job description to analyze
        experiences: List of user Experience objects to evaluate

    Returns:
        String containing stakeholder analysis in markdown format. On error,
        returns an empty string.

    Raises:
        OpenAIQuotaExceededError: If OpenAI API quota is exceeded.
    """
    try:
        if not job_description or not job_description.strip():
            logger.warning("Stakeholder analysis called with empty job description")
            return ""

        experience_summary = _format_experience_for_analysis(experiences)

        config = RunnableConfig(
            tags=[LLMTag.STAKEHOLDER_ANALYSIS.value],
        )

        inputs: StakeholderAnalysisInput = {
            "job_description": job_description,
            "work_experience": experience_summary,
        }

        result = _chain.invoke(inputs, config=config)

        if not result or not result.strip():
            logger.warning("Stakeholder analysis returned empty result from LLM")
            return ""

        return result

    except RateLimitError as exc:
        # Check if this is specifically a quota exceeded error
        error_message = str(exc)
        if "insufficient_quota" in error_message or "exceeded your current quota" in error_message:
            logger.error("OpenAI API quota exceeded during stakeholder analysis: %s", exc)
            raise OpenAIQuotaExceededError() from exc
        # Re-raise other rate limit errors as generic exceptions
        logger.exception("OpenAI rate limit error during stakeholder analysis: %s", exc)
        return ""
    except Exception as exc:
        # Broad catch to prevent errors from bubbling to UI
        logger.exception(
            "Stakeholder analysis failed with exception. Job description length: %d, Experience count: %d, Error: %s",
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
_prompt = get_prompt(PromptName.STAKEHOLDER_ANALYSIS)
_llm = get_model(OpenAIModels.gpt_4o)
_chain = _prompt | _llm | StrOutputParser()
