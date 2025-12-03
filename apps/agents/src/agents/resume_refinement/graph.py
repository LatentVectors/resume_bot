"""Resume refinement agent graph.

Handles AI-assisted resume editing with tool-based update proposals.
This is a stateful agent that requires thread persistence.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import httpx
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.runtime import Runtime, get_runtime

from src.shared.llm import get_openrouter_model
from src.shared.models import ProposedExperience
from src.shared.prompts import PromptName, load_prompt

logger = logging.getLogger(__name__)


# ==================== Runtime Context Schema ====================


@dataclass
class ResumeRefinementContext:
    """Runtime context for resume refinement agent.

    Passed via context_schema when building the graph and accessed
    via Runtime object in nodes and get_runtime() in tools.
    """

    job_id: int
    user_id: int
    gap_analysis: str
    stakeholder_analysis: str
    work_experience: str
    job_description: str
    selected_version_id: int | None
    template_name: str
    parent_version_id: int | None


# ==================== State ====================


class ResumeRefinementState(MessagesState):
    """State for resume refinement agent.

    Uses MessagesState as base which provides 'messages' field.
    Context values are passed via runtime context, not state.
    """

    pass


# ==================== Tool Definitions ====================


@tool
def propose_resume_draft(
    title: str,
    professional_summary: str,
    skills: list[str],
    experiences: list[dict],
    education_ids: list[int],
    certification_ids: list[int],
) -> dict:
    """Propose a complete resume draft.

    Creates a new resume version with the proposed content. Each call must include
    complete resume data (title, summary, skills, all experiences with bullet points).

    Args:
        title: Professional title/headline for the resume.
        professional_summary: Professional summary tailored to the job.
        skills: List of skills relevant to the position.
        experiences: Complete list of experiences to include in resume.
            Each experience should have: experience_id (int), title (str), points (list[str]).
        education_ids: List of education record IDs to include in resume.
        certification_ids: List of certification record IDs to include in resume.

    Returns:
        Dict with version_id, version_index, and confirmation message.
    """
    try:
        # Access runtime context
        runtime = get_runtime(ResumeRefinementContext)

        # Parse experiences into ProposedExperience models
        parsed_experiences = []
        for exp in experiences:
            parsed_experiences.append(
                ProposedExperience(
                    experience_id=exp["experience_id"],
                    title=exp["title"],
                    points=exp["points"],
                )
            )

        # Build request payload matching FastAPI ResumeCreate schema
        payload = {
            "template_name": runtime.context.template_name,
            "event_type": "generate",
            "parent_version_id": runtime.context.parent_version_id,
            "resume_json": {
                "name": "",  # Will be filled by backend from user record
                "title": title,
                "email": "",
                "phone": "",
                "linkedin_url": "",
                "professional_summary": professional_summary,
                "skills": skills,
                "experience": [
                    {
                        "experience_id": exp.experience_id,
                        "title": exp.title,
                        "points": exp.points,
                    }
                    for exp in parsed_experiences
                ],
                "education_ids": education_ids,
                "certification_ids": certification_ids,
            },
        }

        # Call FastAPI backend to persist the version
        api_base = os.getenv("FASTAPI_BASE_URL", "http://localhost:8000")
        response = httpx.post(
            f"{api_base}/api/v1/jobs/{runtime.context.job_id}/resumes",
            json=payload,
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()

        logger.info(
            f"Created resume draft: version_id={result['id']}, version_index={result['version_index']}"
        )

        return {
            "version_id": result["id"],
            "version_index": result["version_index"],
            "message": f"Resume Draft Created: v{result['version_index']}",
        }

    except httpx.HTTPStatusError as exc:
        logger.exception(f"HTTP error creating resume draft: {exc}")
        return {
            "error": f"Failed to create resume draft: HTTP {exc.response.status_code}",
            "message": "I encountered an error saving the resume draft. Please try again.",
        }
    except Exception as exc:
        logger.exception(f"Error creating resume draft: {exc}")
        return {
            "error": str(exc),
            "message": "I encountered an error saving the resume draft. Please try again.",
        }


# ==================== Prompt Loading ====================


def _get_system_prompt() -> str:
    """Load the system prompt from the JSON file.

    Returns:
        The system prompt string.
    """
    prompt_template = load_prompt(PromptName.RESUME_ALIGNMENT_WORKFLOW)
    # Extract system message from the template
    for message in prompt_template.messages:
        if hasattr(message, "prompt") and hasattr(message.prompt, "template"):
            # Check if this is the system message (first message)
            return message.prompt.template
    raise ValueError("Could not extract system prompt from template")


def _get_user_prompt_template() -> str:
    """Load the user prompt template from the JSON file.

    Returns:
        The user prompt template string.
    """
    prompt_template = load_prompt(PromptName.RESUME_ALIGNMENT_WORKFLOW)
    # Extract user message from the template (second message)
    messages = list(prompt_template.messages)
    if len(messages) >= 2:
        user_msg = messages[1]
        if hasattr(user_msg, "prompt") and hasattr(user_msg.prompt, "template"):
            return user_msg.prompt.template
    raise ValueError("Could not extract user prompt from template")


# ==================== Graph Nodes ====================


def call_model(
    state: ResumeRefinementState, runtime: Runtime[ResumeRefinementContext]
) -> dict:
    """Call the LLM with tools bound.

    Args:
        state: Current state with messages.
        runtime: Runtime context with job details.

    Returns:
        Updated state with AI response.
    """
    try:
        # Initialize LLM with tools
        llm = get_openrouter_model("google/gemini-2.5-pro")
        llm_with_tools = llm.bind_tools([propose_resume_draft])

        # Load prompts
        system_prompt = _get_system_prompt()
        user_prompt_template = _get_user_prompt_template()

        # Format user prompt with context
        user_prompt = user_prompt_template.format(
            work_experience=runtime.context.work_experience,
            job_description=runtime.context.job_description,
            gap_analysis=runtime.context.gap_analysis,
            stakeholder_analysis=runtime.context.stakeholder_analysis,
        )

        # Build the prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("user", user_prompt),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        # Build chain and invoke
        chain = prompt | llm_with_tools
        response = chain.invoke({"messages": state["messages"]})

        return {"messages": [response]}

    except Exception as exc:
        logger.exception(f"Error calling model: {exc}")
        # Graceful degradation: return an error message
        error_message = AIMessage(
            content="I apologize, but I encountered an error processing your request. Please try again."
        )
        return {"messages": [error_message]}


# ==================== Graph Definition ====================


def build_graph() -> StateGraph:
    """Build the resume refinement graph."""
    # Create tools list
    tools = [propose_resume_draft]

    # Build the graph with context schema
    builder = StateGraph(ResumeRefinementState, context_schema=ResumeRefinementContext)

    # Add nodes
    builder.add_node("call_model", call_model)
    builder.add_node("tools", ToolNode(tools))

    # Add edges
    builder.add_edge(START, "call_model")

    # Conditional edge: if tool calls exist, go to tools node, else END
    builder.add_conditional_edges(
        "call_model",
        tools_condition,
        {"tools": "tools", END: END},
    )

    # After tools, return to model
    builder.add_edge("tools", "call_model")

    return builder.compile()


# Compiled graph for LangGraph deployment
graph = build_graph()

