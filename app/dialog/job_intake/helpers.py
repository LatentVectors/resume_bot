"""Shared helper functions and tools for job intake flow."""

from __future__ import annotations

from typing import Annotated

from langchain_core.tools import tool

from src.features.jobs.gap_analysis import GapAnalysisReport


def format_gap_analysis_message(gap_report: GapAnalysisReport) -> str:
    """Format gap analysis report as a readable message.

    Args:
        gap_report: The gap analysis report to format.

    Returns:
        Formatted message string.
    """
    if gap_report.has_error:
        return "⚠️ I encountered an issue analyzing the job requirements. Let's discuss your experience anyway."

    sections = ["📊 **Job Requirements Analysis**\n"]

    if gap_report.matched_requirements:
        sections.append("✅ **Strong Matches:**")
        for match in gap_report.matched_requirements:
            sections.append(f"- {match.requirement}: {match.evidence}")
        sections.append("")

    if gap_report.partial_matches:
        sections.append("🔶 **Partial Matches:**")
        for partial in gap_report.partial_matches:
            sections.append(f"- {partial.requirement}")
            sections.append(f"  - What matches: {partial.what_matches}")
            sections.append(f"  - What's missing: {partial.what_is_missing}")
        sections.append("")

    if gap_report.gaps:
        sections.append("❌ **Gaps:**")
        for gap in gap_report.gaps:
            sections.append(f"- {gap.requirement}: {gap.why_missing}")
        sections.append("")

    if gap_report.suggested_questions:
        sections.append("💡 **Let's explore:**")
        for question in gap_report.suggested_questions[:3]:  # Limit to top 3
            sections.append(f"- {question}")

    return "\n".join(sections)


# ==================== Tool Definitions ====================


@tool
def propose_experience_update(
    experience_id: Annotated[int, "ID of the experience to update"],
    company_overview: Annotated[str | None, "Overview of the company"] = None,
    role_overview: Annotated[str | None, "Overview of the role"] = None,
    skills: Annotated[list[str] | None, "List of skills used in this role"] = None,
) -> str:
    """Propose an update to an existing experience record.

    This tool allows the AI to suggest updates to company overview, role overview,
    or skills for an experience. The user will review and can accept or reject.

    Args:
        experience_id: ID of the experience to update.
        company_overview: Proposed company overview text.
        role_overview: Proposed role overview text.
        skills: Proposed list of skills.

    Returns:
        Confirmation message for the AI.
    """
    return f"Proposal created for experience {experience_id}"


@tool
def propose_achievement_update(
    achievement_id: Annotated[int, "ID of the achievement to update"],
    title: Annotated[str, "Updated achievement title/headline"],
    content: Annotated[str, "Updated achievement content"],
) -> str:
    """Propose an update to an existing achievement.

    Args:
        achievement_id: ID of the achievement to update.
        title: Proposed new title for the achievement.
        content: Proposed new content for the achievement.

    Returns:
        Confirmation message for the AI.
    """
    return f"Proposal created for achievement {achievement_id}"


@tool
def propose_new_achievement(
    experience_id: Annotated[int, "ID of the experience to add achievement to"],
    title: Annotated[str, "Achievement title/headline"],
    content: Annotated[str, "Achievement content"],
    order: Annotated[int | None, "Order/position in the list"] = None,
) -> str:
    """Propose adding a new achievement to an experience.

    Args:
        experience_id: ID of the parent experience.
        title: Proposed achievement title.
        content: Proposed achievement content.
        order: Optional order position.

    Returns:
        Confirmation message for the AI.
    """
    return f"Proposal created for new achievement on experience {experience_id}"


# Tool list for binding
EXPERIENCE_TOOLS = [propose_experience_update, propose_achievement_update, propose_new_achievement]

# System prompts
EXPERIENCE_SYSTEM_PROMPT = """You are an expert career coach helping a candidate prepare their experience for a job application.

Your role:
1. Ask thoughtful questions to uncover additional context about their experience
2. Help them articulate achievements and impact in their previous roles
3. Identify relevant skills and experiences that match job requirements
4. Propose specific updates to their experience records when appropriate

Guidelines:
- Be conversational and encouraging
- Ask one or two questions at a time, don't overwhelm
- When you learn something relevant, propose a specific update using your tools
- Focus on quantifiable achievements and impact
- Help translate their experience into language that matches the job requirements

Tools available:
- propose_experience_update: Update company overview, role overview, or skills for an experience
- propose_achievement_update: Modify an existing achievement (requires title and content)
- propose_new_achievement: Add a new achievement to an experience (requires title and content)

The user will review your proposals and can accept (saves to database) or reject them.

Current job description:
{job_description}

Current experience records:
{experience_summary}
"""

SUMMARIZATION_SYSTEM_PROMPT = """You are an expert career coach summarizing a conversation about a candidate's experience.

Extract key insights from the conversation, focusing on:
- Additional context provided beyond the written experience records
- Unique details, motivations, and interests expressed
- The candidate's fit assessment based on gap analysis and responses
- Clarifications or nuances that refine understanding of their background

Provide a concise summary in 2-4 paragraphs that will help tailor their resume to the job.
"""
