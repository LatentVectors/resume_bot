"""Stakeholder analysis feature for understanding hiring manager perspectives.

This module provides functionality to analyze who the hiring stakeholders are,
what they're looking for, and how they may perceive the candidate's background.
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.constants import LLMTag
from app.shared.formatters import format_experience_with_achievements
from src.core.models import OpenAIModels, get_model
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
    """
    try:
        if not job_description or not job_description.strip():
            logger.warning("Stakeholder analysis called with empty job description")
            return ""

        experience_summary = _format_experience_for_analysis(experiences)

        config = RunnableConfig(
            tags=[LLMTag.STAKEHOLDER_ANALYSIS.value],
        )

        result = _chain.invoke(
            {
                "job_description": job_description,
                "work_experience": experience_summary,
            },
            config=config,
        )

        if not result or not result.strip():
            logger.warning("Stakeholder analysis returned empty result from LLM")
            return ""

        return result

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


_SYSTEM_PROMPT = """
# **Stakeholder Analysis - Placeholder**

## **Objective**

Analyze the key hiring stakeholders for this position and provide insights into their
likely perspectives on the candidate's background.

## **Instructions**

1. Identify the key hiring stakeholders based on the job description (hiring manager, 
   team members, executives, etc.)
2. For each stakeholder, describe:
   - Their likely priorities and concerns
   - How they may perceive the candidate's background
   - Potential objections or questions they may have
3. Provide strategic recommendations for addressing stakeholder concerns

## **Output Format**

Provide your analysis in clear markdown format with appropriate sections and bullet points.

**Note:** This is a placeholder prompt. Production prompt will be added in a follow-up update.
"""

_USER_PROMPT = """
<job_description>
{job_description}
</job_description>

<work_experience>
{work_experience}
</work_experience>

Analyze the key stakeholders for this position and their likely perspectives on the candidate.
"""


# Model and chain setup
_llm = get_model(OpenAIModels.gpt_4o)
_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("user", _USER_PROMPT),
        ]
    )
    | _llm
    | StrOutputParser()
)

