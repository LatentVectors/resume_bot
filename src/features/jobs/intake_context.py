"""Intake context summarization and resume generation from conversation.

This module provides functionality to summarize intake conversations and generate
initial resume drafts enriched with conversational context from the job intake flow.
"""

from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from openai import APIConnectionError

from app.constants import LLMTag
from app.shared.formatters import format_experience_with_achievements
from src.core.models import OpenAIModels, get_model
from src.features.jobs.gap_analysis import GapAnalysisReport
from src.features.resume.data_adapter import fetch_experience_data, fetch_user_data, transform_user_to_resume_data
from src.features.resume.types import ResumeData
from src.logging_config import logger

_SUMMARIZATION_SYSTEM_PROMPT = """You are an expert career coach who excels at extracting meaningful insights from conversations.

Your task is to analyze a job intake conversation between a user and an AI assistant, along with a gap analysis report, and create a concise summary that captures:

1. **Additional Context**: Information the user shared beyond what's in their written experience records (motivations, interests, working style, values, specific achievements not formally documented)

2. **Unique Details**: Specific examples, anecdotes, or clarifications that reveal deeper understanding of their background and capabilities

3. **Fit Assessment**: How the user's experience and expressed interests align with the job requirements based on both the gap analysis and conversation

4. **Key Clarifications**: Important nuances or corrections to initial assumptions about their background

Your summary should be 2-4 paragraphs that will be used to enrich the resume generation process. Focus on actionable insights that help create a more targeted, authentic resume.

If the conversation is very brief or contains no substantive information, still provide a short summary noting what was discussed or that minimal additional context was provided.
"""

_SUMMARIZATION_USER_PROMPT = """Gap Analysis Report:
Matched Requirements: {matched_requirements}
Partial Matches: {partial_matches}
Gaps: {gaps}

Conversation History:
{conversation_history}

Create a concise summary (2-4 paragraphs) extracting key insights from this intake conversation.
"""


def _format_messages_for_summary(messages: list[dict]) -> str:
    """Format LangChain message history into readable text.

    Args:
        messages: List of message dictionaries in LangChain format

    Returns:
        Formatted string representation of the conversation
    """
    if not messages:
        return "No conversation messages."

    formatted_parts: list[str] = []

    for msg in messages:
        # Handle different LangChain message formats
        msg_type = msg.get("type", "unknown")
        content = msg.get("content", "")

        if msg_type == "human" or msg_type == "user":
            formatted_parts.append(f"User: {content}")
        elif msg_type == "ai" or msg_type == "assistant":
            formatted_parts.append(f"AI: {content}")
        elif msg_type == "system":
            formatted_parts.append(f"System: {content}")
        else:
            # Generic fallback
            formatted_parts.append(f"{msg_type.title()}: {content}")

    return "\n\n".join(formatted_parts)


def _format_gap_analysis_for_summary(gap_analysis: GapAnalysisReport) -> dict[str, str]:
    """Format gap analysis report for use in summary prompt.

    Args:
        gap_analysis: The gap analysis report

    Returns:
        Dictionary with formatted lists for matched, partial, and gaps
    """
    matched = "\n".join(f"- {req.requirement}: {req.evidence}" for req in gap_analysis.matched_requirements)
    partial = "\n".join(
        f"- {pm.requirement}\n  Matches: {pm.what_matches}\n  Missing: {pm.what_is_missing}"
        for pm in gap_analysis.partial_matches
    )
    gaps = "\n".join(f"- {gap.requirement}: {gap.why_missing}" for gap in gap_analysis.gaps)

    return {
        "matched_requirements": matched or "None identified",
        "partial_matches": partial or "None identified",
        "gaps": gaps or "None identified",
    }


# Model and chain setup for summarization
_llm = get_model(OpenAIModels.gpt_4o)
_llm_with_retry = _llm.with_retry(retry_if_exception_type=(APIConnectionError,))
_summarization_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", _SUMMARIZATION_SYSTEM_PROMPT),
            ("user", _SUMMARIZATION_USER_PROMPT),
        ]
    )
    | _llm_with_retry
)


def summarize_intake_conversation(messages: list[dict], gap_analysis: GapAnalysisReport) -> str:
    """Summarize key insights from intake conversation.

    Extracts and synthesizes:
    - Additional context beyond written experience
    - Unique details, motivations, interests expressed
    - Fit assessment based on gap analysis and responses
    - Clarifications refining understanding of background

    Args:
        messages: Full chat history from intake step 2 (LangChain format)
        gap_analysis: The gap analysis report from intake step 2

    Returns:
        Concise summary (2-4 paragraphs) as string. On error, returns a minimal
        fallback summary indicating the conversation could not be processed.
    """
    try:
        conversation_history = _format_messages_for_summary(messages)
        gap_analysis_formatted = _format_gap_analysis_for_summary(gap_analysis)

        config = RunnableConfig(
            tags=[LLMTag.INTAKE_SUMMARIZATION.value],
        )

        result = _summarization_chain.invoke(
            {
                "conversation_history": conversation_history,
                **gap_analysis_formatted,
            },
            config=config,
        )

        # Extract content from AIMessage
        if hasattr(result, "content"):
            summary = result.content.strip()
        else:
            summary = str(result).strip()

        logger.info("Successfully summarized intake conversation", extra={"summary_length": len(summary)})
        return summary

    except Exception as exc:
        logger.exception("Failed to summarize intake conversation: %s", exc)
        # Return minimal fallback summary
        return (
            "Unable to generate detailed conversation summary due to processing error. "
            "The user engaged in a job intake conversation about their experience and fit for the role."
        )


def generate_resume_from_conversation(
    job_id: int,
    user_id: int,
    conversation_summary: str,
    chat_history: list[dict],
) -> ResumeData:
    """Generate initial resume draft using intake conversation context.

    This function is specifically for the intake flow and does NOT use
    Response records (those are out of scope for this sprint).

    Args:
        job_id: ID of the job being applied to
        user_id: ID of the user
        conversation_summary: Summary from summarize_intake_conversation()
        chat_history: Full chat history from intake step 2 (may be used for future enhancements)

    Returns:
        ResumeData ready for creating first version in intake step 3

    Raises:
        ValueError: If job or user data is invalid or missing
    """
    from src.agents.main import InputState, OutputState, create_experience, main_agent
    from src.agents.main.state import Experience as AgentExperience
    from src.database import db_manager

    try:
        # Fetch job
        job = db_manager.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Fetch user data and experiences
        user_data = fetch_user_data(user_id)
        if not user_data:
            raise ValueError(f"User {user_id} not found")

        experiences = fetch_experience_data(user_id)
        if not experiences:
            raise ValueError("At least one experience record is required to generate a resume")

        # Create base resume from user profile
        base_resume = transform_user_to_resume_data(
            user_data=user_data,
            experience_data=experiences,
            job_title=job.job_title or "",
        )

        # Prepare agent experiences (include achievements if available)
        agent_experiences: list[AgentExperience] = []
        for exp in experiences:
            # Fetch achievements for this experience
            achievements = db_manager.list_experience_achievements(exp.id)

            # Use the standardized formatter to create content string
            full_content = format_experience_with_achievements(exp, achievements)

            agent_experiences.append(
                create_experience(
                    id=str(exp.id or ""),
                    company=exp.company_name,
                    title=exp.job_title,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    content=full_content,
                    points=[],
                    location=exp.location or "",
                )
            )

        # Build InputState with conversation summary as "responses"
        # This enriches the resume generation with insights from the intake conversation
        initial_state = InputState(
            job_description=job.job_description,
            experiences=agent_experiences,
            responses=conversation_summary,  # Key: pass summary as responses field
            special_instructions=None,
            resume_draft=base_resume,
        )

        config = RunnableConfig(
            tags=[LLMTag.RESUME_GENERATION.value],
            metadata={"job_id": job_id, "user_id": user_id, "source": "intake_flow"},
        )

        # Invoke the resume generation agent
        result = main_agent.invoke(initial_state, config=config)
        output = OutputState.model_validate(result)

        if not output.resume_data:
            raise ValueError("Agent did not return resume_data")

        logger.info(
            "Successfully generated resume from intake conversation",
            extra={"job_id": job_id, "user_id": user_id, "experience_count": len(agent_experiences)},
        )

        return output.resume_data

    except Exception as exc:
        logger.exception("Failed to generate resume from conversation: %s", exc)
        raise
