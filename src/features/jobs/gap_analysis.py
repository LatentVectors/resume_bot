"""Gap analysis feature for matching job requirements to user experience.

This module provides functionality to analyze the fit between a job description
and a user's experience, identifying matched requirements, partial matches, gaps,
and suggesting clarifying questions.
"""

from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from openai import APIConnectionError
from pydantic import BaseModel, Field

from app.constants import LLMTag
from app.shared.formatters import format_experience_with_achievements
from src.core.models import OpenAIModels, get_model
from src.database import Experience, db_manager
from src.logging_config import logger


class MatchedRequirement(BaseModel):
    """A job requirement that is fully matched by user experience."""

    requirement: str = Field(description="The specific job requirement")
    evidence: str = Field(description="Summary of experience that demonstrates this requirement")


class PartialMatch(BaseModel):
    """A job requirement that is partially matched by user experience."""

    requirement: str = Field(description="The specific job requirement")
    what_matches: str = Field(description="What aspects of the requirement are covered by experience")
    what_is_missing: str = Field(description="What aspects of the requirement are not clearly demonstrated")


class Gap(BaseModel):
    """A job requirement with no clear match in user experience."""

    requirement: str = Field(description="The specific job requirement")
    why_missing: str = Field(description="Explanation of why this requirement is not met by current experience")


class GapAnalysisReport(BaseModel):
    """Complete gap analysis report for a job-experience fit."""

    matched_requirements: list[MatchedRequirement] = []
    partial_matches: list[PartialMatch] = []
    gaps: list[Gap] = []
    suggested_questions: list[str] = Field(
        default=[],
        description="Questions to ask the user to clarify or expand their experience",
    )
    has_error: bool = Field(
        default=False,
        description="True if the analysis failed due to an error",
    )


_SYSTEM_PROMPT = """You are an expert career coach analyzing how well a candidate's experience matches a job description.

Your task is to:
1. Extract key requirements from the job description (skills, experience, qualifications, responsibilities)
2. Match each requirement against the candidate's work experience
3. Categorize each requirement as:
   - MATCHED: Clear evidence in experience that meets the requirement
   - PARTIAL: Some relevant experience but gaps or uncertainties remain
   - GAP: No clear evidence in experience for this requirement
4. Generate thoughtful questions to help clarify or expand the candidate's experience

Be thorough but concise. Focus on substantive requirements, not generic qualities.
Consider both explicit requirements and implicit needs suggested by the job description.

For suggested_questions, ask about:
- Experiences that might fill identified gaps
- Details that could strengthen partial matches
- Context that might reveal hidden relevant experience
- Achievements or projects related to key requirements
"""

_USER_PROMPT = """Job Description:
{job_description}

Candidate's Experience:
{experience_summary}

Analyze the fit between this job and the candidate's experience.
"""


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


# Model and chain setup
_llm = get_model(OpenAIModels.gpt_4o)
_llm_structured = _llm.with_structured_output(GapAnalysisReport).with_retry(
    retry_if_exception_type=(APIConnectionError,)
)
_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("user", _USER_PROMPT),
        ]
    )
    | _llm_structured
)


def analyze_job_experience_fit(job_description: str, experiences: list[Experience]) -> GapAnalysisReport:
    """Analyze how well user experiences match a job description.

    Uses an LLM to extract job requirements and match them against user experience,
    producing a structured report of matches, partial matches, gaps, and suggested
    questions for further clarification.

    Args:
        job_description: The full text of the job description to analyze
        experiences: List of user Experience objects to evaluate

    Returns:
        GapAnalysisReport containing matched requirements, partial matches, gaps,
        and suggested questions. On error, returns a report with has_error=True
        and empty lists.
    """
    try:
        experience_summary = _format_experience_for_analysis(experiences)

        config = RunnableConfig(
            tags=[LLMTag.GAP_ANALYSIS.value],
        )

        result = _chain.invoke(
            {
                "job_description": job_description,
                "experience_summary": experience_summary,
            },
            config=config,
        )

        # Safety: validate the result to ensure it matches our schema
        if isinstance(result, dict):
            validated = GapAnalysisReport.model_validate(result)
        else:
            validated = result

        return validated

    except Exception as exc:
        # Broad catch to prevent errors from bubbling to UI
        logger.exception("Gap analysis failed: %s", exc)
        return GapAnalysisReport(
            matched_requirements=[],
            partial_matches=[],
            gaps=[],
            suggested_questions=[],
            has_error=True,
        )
