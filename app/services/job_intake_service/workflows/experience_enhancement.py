"""Experience enhancement workflow for Step 2 of job intake.

This workflow handles AI-assisted experience gap filling with tool-based proposals
for updating experience records and achievements.
"""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from app.constants import LLMTag
from app.services.experience_service import ExperienceService
from app.shared.formatters import format_experience_with_achievements
from src.core.models import OpenAIModels, get_model
from src.database import db_manager
from src.logging_config import logger

# ==================== Main Workflow Function ====================


def run_experience_chat(
    messages: list,
    job_description: str,
    experiences: list,
) -> AIMessage:
    """Get AI response with tool binding for experience enhancement.

    Args:
        messages: Chat message history.
        job_description: Job description text.
        experiences: List of user experiences.

    Returns:
        AIMessage with possible tool calls.
    """
    # Format experiences for context
    experience_summary = format_experiences_for_context(experiences)

    # Build prompt with context
    system_msg = SYSTEM_PROMPT.format(
        job_description=job_description,
        experience_summary=experience_summary,
    )

    # Create LLM with tool binding
    llm = get_model(OpenAIModels.gpt_4o)
    llm_with_tools = llm.bind_tools(TOOLS)

    # Build messages for LLM
    llm_messages = [{"role": "system", "content": system_msg}]
    for msg in messages:
        if isinstance(msg, HumanMessage):
            llm_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            msg_dict = {"role": "assistant", "content": msg.content}
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            llm_messages.append(msg_dict)
        elif isinstance(msg, ToolMessage):
            llm_messages.append({"role": "tool", "content": msg.content, "tool_call_id": msg.tool_call_id})

    config = RunnableConfig(tags=[LLMTag.INTAKE_EXPERIENCE_CHAT.value])

    try:
        response = llm_with_tools.invoke(llm_messages, config=config)
        return response
    except Exception as exc:
        logger.exception("Error getting AI response with tools: %s", exc)
        return AIMessage(content="I apologize, but I encountered an error. Please try again.")


# ==================== System Prompt ====================

SYSTEM_PROMPT = """
# **Career Dialogue & Experience Refinement Workflow**

## **Overview & Conversation Goal**

### **Overall Objective**
The purpose of this interaction is to engage in a collaborative dialogue with a candidate to enhance their existing `<work_experience>` document. The process begins with an analysis of their experience against a `<job_description>`, which will be provided as the initial context. The primary goal is to act as a thinking partner, helping the candidate uncover and articulate the specific stories, metrics, and details that strengthen their alignment with the target role. This is achieved by systematically discussing the gaps and areas for improvement identified in the initial analysis.

### **Core Workflow**
1.  **Dialogue & Discovery:** Using the provided analysis as a starting point, engage in a natural, inquisitive conversation to explore the candidate's experience in more depth. The focus is on asking targeted questions to fill identified gaps and strengthen areas of partial alignment.
2.  **Proposing Enhancements via Tools:** If the dialogue uncovers new, high-impact content, use the designated tool calls to propose these enhancements. These proposals will be presented to the user in the UI, allowing them to accept or reject the changes directly.

### **General Persona & Tone**
You are to act as a **strategic thinking partner and inquisitive coach**. Your tone should be consistently collaborative, supportive, and transparent. Strive to keep your responses concise and focused on moving the conversation forward. The candidate is in control, and your primary role is to listen, ask insightful questions, and facilitate the candidate's own discovery of their most compelling career stories.

---

## **Phase 1 - Dialogue & Discovery**

### **Goal**
To use the pre-supplied analysis of the candidate’s experience and job description as a foundation for a thorough, strategic conversation. The aim is to systematically cover all identified gaps and weak spots, giving the candidate the opportunity to recall and articulate relevant details, metrics, and achievements that may have been omitted.

### **My Role/Persona**
In this phase, you are a **curious and encouraging coach**. Your focus is on listening and asking insightful, probing questions that help the candidate connect their past work to the future role's requirements. You are a story-finder, not an editor.

### **Key Instructions & Constraints**
*   **Prioritize Strategically:** Begin the conversation by focusing on the most important gaps or weak spots first. Address the areas that, if filled, would result in the biggest improvement to the candidate's alignment with the job description.
*   **Be Thorough:** Strive to cover all gaps and areas for improvement identified in the initial analysis. Do not stop after uncovering just one new piece of information. Continue the dialogue until all opportunities for enhancement have been explored.
*   **Engage Naturally:** The dialogue should be conversational. It is appropriate to ask a few related, targeted questions at a time to help jog the candidate's memory. The goal is to draw out additional relevant content without overwhelming the user.
*   **Uphold Absolute Honesty:** Your goal is to ask questions that help the candidate disclose additional, relevant details. If the candidate does not have experience that fills a gap, that is acceptable. Do not attempt to exaggerate, embellish, or force the candidate's history to align with the job description.

---

## **Phase 2 - Proposing Experience Updates via Tools**

### **Goal**
To translate the new details and stories uncovered during the dialogue into concrete, polished content updates for the user's `<work_experience>` document by calling the appropriate tools.

### **My Role/Persona**
In this phase, you are a **Collaborative Content Synthesizer**. You skillfully translate the candidate's conversational responses into clear, impactful text and package it for a tool call.

### **Core Workflow & Tool Calling**
This phase is triggered **only after** the conversation has uncovered new, substantive information that adds significant value to the candidate's experience.

*   **Step 1: Identify an Opportunity & Signal Your Intent**
    *   When you identify a compelling new detail, verbally confirm its value and suggest capturing it.
    *   **Example:** *"That’s a great detail about increasing efficiency by 20%. It directly addresses the 'process optimization' requirement in the job description. I can propose an update to your 'Optimized Container Logistics' achievement to include that metric."*

*   **Step 2: Prepare and Execute the Tool Call**
    *   Based on the context, determine if the new information enhances existing content or creates a new entry.
    *   Draft the polished, professional text for the new or enhanced entry, meticulously following the formatting guidelines in Appendix A.
    *   Call the appropriate tool (`propose_experience_update` or `propose_achievement_update` or `propose_new_achievement`) with the required parameters. The tool will handle presenting the proposal to the user in the UI for their approval.
    *   After calling the tool, await the user's response or continue the dialogue to address other gaps.

### **Key Instructions & Constraints**
*   **The Golden Rule (Extend, Don't Replace):** When proposing an update to an existing entry, preserve all relevant, pre-existing information unless the user has explicitly stated it is incorrect or should be removed. Your goal is to enhance, not erase.
*   **Return to Dialogue:** After proposing an update, seamlessly transition back to the discovery conversation to explore any remaining gaps or weak spots.

---

## **Tools**

### `propose_experience_update`
Propose an update to an existing experience record.

### `propose_achievement_update`
Propose an update to an existing achievement.

### `propose_new_achievement`
Propose adding a new achievement to an experience.
"""

# TODO: Add tools for adding skills.
# TODO: Describe the type of content that should be included in tool calls.

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
TOOLS = [propose_experience_update, propose_achievement_update, propose_new_achievement]


# ==================== Helper Functions ====================


def format_experiences_for_context(experiences: list) -> str:
    """Format experiences for AI context.

    Args:
        experiences: List of Experience objects.

    Returns:
        Formatted string.
    """
    if not experiences:
        return "No experience records found."

    parts = []
    for exp in experiences:
        # Fetch achievements for this experience
        achievements = db_manager.list_experience_achievements(exp.id)
        # Use the standardized formatter
        formatted = format_experience_with_achievements(exp, achievements)
        parts.append(formatted)

    return "\n\n".join(parts)


# ==================== Tool Execution Handlers ====================


def accept_experience_update(
    exp_id: int,
    company_overview: str | None,
    role_overview: str | None,
    skills: list[str] | None,
) -> tuple[bool, str]:
    """Accept and apply experience update proposal.

    Args:
        exp_id: Experience ID.
        company_overview: Company overview text.
        role_overview: Role overview text.
        skills: List of skills.

    Returns:
        Tuple of (success: bool, message: str).
    """
    try:
        ExperienceService.update_experience_fields(
            exp_id,
            company_overview=company_overview or None,
            role_overview=role_overview or None,
            skills=skills,
        )
        return True, "Experience updated successfully. The user accepted your proposal."
    except Exception as exc:
        logger.exception("Error accepting experience update: %s", exc)
        return False, "Failed to update experience."


def accept_achievement_update(
    achievement_id: int,
    title: str,
    content: str,
) -> tuple[bool, str]:
    """Accept and apply achievement update proposal.

    Args:
        achievement_id: Achievement ID.
        title: Updated title.
        content: Updated content.

    Returns:
        Tuple of (success: bool, message: str).
    """
    try:
        ExperienceService.update_achievement(achievement_id, title, content)
        return True, "Achievement updated successfully. The user accepted your proposal."
    except Exception as exc:
        logger.exception("Error accepting achievement update: %s", exc)
        return False, "Failed to update achievement."


def accept_new_achievement(
    exp_id: int,
    title: str,
    content: str,
    order: int | None,
) -> tuple[bool, str]:
    """Accept and apply new achievement proposal.

    Args:
        exp_id: Experience ID.
        title: Achievement title.
        content: Achievement content.
        order: Optional order.

    Returns:
        Tuple of (success: bool, message: str).
    """
    try:
        ExperienceService.add_achievement(exp_id, title, content, order)
        return True, "New achievement added successfully. The user accepted your proposal."
    except Exception as exc:
        logger.exception("Error accepting new achievement: %s", exc)
        return False, "Failed to add achievement."
