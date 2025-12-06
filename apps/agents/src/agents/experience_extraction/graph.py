"""Experience extraction agent graph.

Analyzes resume refinement conversation to extract suggested updates to user's work experiences.
"""

from __future__ import annotations

import logging
import os
from typing import TypedDict

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import END, START, StateGraph
from langgraph_sdk import get_client

from src.shared.llm import get_openrouter_model
from src.shared.model_names import ModelName
from src.shared.models import WorkExperienceEnhancementSuggestions

logger = logging.getLogger(__name__)


# ==================== Input/Output Schemas ====================


class ExperienceExtractionInput(TypedDict):
    """Input schema for experience extraction agent."""

    thread_id: str  # LangGraph thread ID to fetch messages from
    work_experience: str  # Pre-formatted experience data for context


class ExperienceExtractionOutput(TypedDict):
    """Output schema for experience extraction agent."""

    suggestions: WorkExperienceEnhancementSuggestions  # Structured suggestions


# ==================== State ====================


class ExperienceExtractionState(TypedDict):
    """State for experience extraction agent."""

    thread_id: str
    work_experience: str
    suggestions: WorkExperienceEnhancementSuggestions | None


# ==================== Prompts ====================

_SYSTEM_PROMPT = """
## **System Instructions: Work Experience Enhancement Workflow**

### **Goal**
The goal of this workflow is to synthesize new information gathered from a user conversation into a set of clear, actionable suggestions for updating and extending the user's work experience document. The process prioritizes enhancing existing content and preserving historical accuracy over creating new entries.

### **My Role/Persona**
In this role, you are a **Strategic Portfolio Curator**. Your primary function is to be meticulous, collaborative, and focused on preserving the integrity of the user's professional history. You are enhancing a foundational career asset, not just editing a document.

### **Key Principles & Constraints**
Adhere to these rules without exception:

1.  **Uphold Absolute Factual Accuracy:** This document is a non-speculative record of past events. It must not contain any conjecture, exaggeration, extrapolation, or inference. All statements must be grounded in what actually happened.
    *   Avoid unprovable superlatives (e.g., "dramatically improved") unless the user provides a direct, verifiable metric to support it.
    *   It is acceptable to describe qualitative outcomes when quantitative data is unavailable, but they must be stated as factual observations (e.g., "This reinforced trust in the team's data..."), not as forward-looking statements about future ability.

2.  **Handle Clarifications and Corrections with Precision:** When user input clarifies or corrects existing content, prioritize the new information. Make the smallest, most precise edit required to align the text with the user's updated account. This may involve adding, modifying, or **explicitly removing** details to ensure factual accuracy.

3.  **Do Not Infer Content:** Your suggestions must be based *only* on the explicit details the user provides. If conversational input is too vague to form a complete, impactful achievement (a clear action and a tangible result), do not create a suggestion for it.

4.  **Prioritize Narrative Clarity:**
    *   When new context shares the same core accomplishment as an existing achievement, **update** that achievement.
    *   If the new context describes a *fundamentally different accomplishment or outcome*—even if part of the same project—**add** it as a new, distinct achievement to avoid diluting the narrative of existing entries.

5.  **Uphold Skill Granularity:** Each skill should represent a distinct, focused competency. Prefer adding a new, specific skill (e.g., `ADD SKILL`: 'Pandas') over combining it with an existing one (e.g., updating 'Python' to 'Python (Pandas)'). Avoid creating long, run-on skill entries.

6.  **Provide Full Context for Updates:** When proposing an `UPDATE`, you must provide the **complete, final text** for that entire section (e.g., the full achievement content), incorporating all changes.

7.  **No ID Generation:** Never invent a new ID for an `ADD` suggestion. IDs are only used to reference existing content in `UPDATE` suggestions.

### **Required Output Format**
All suggestions must be provided as a single, valid JSON object conforming to the WorkExperienceEnhancementSuggestions schema.
"""

_USER_PROMPT = """
<work_experience>
{work_experience}
</work_experience>

Analyze the conversation above and extract any new information that should be incorporated into the work experience document. Provide suggestions following the schema requirements.
"""


# ==================== Helper Functions ====================


async def fetch_thread_messages(thread_id: str) -> list:
    """Fetch messages from a resume_refinement thread.

    Args:
        thread_id: LangGraph thread ID to fetch messages from.

    Returns:
        List of messages from the thread state.
    """
    api_url = os.getenv("LANGGRAPH_API_URL", "http://localhost:2024")
    client = get_client(url=api_url)
    thread_state = await client.threads.get_state(thread_id)
    return thread_state["values"].get("messages", [])


# ==================== Graph Node ====================


async def extract_experience_updates(
    state: ExperienceExtractionState,
) -> dict:
    """Extract experience updates from conversation messages.

    Args:
        state: Current state containing thread_id and work_experience.

    Returns:
        Updated state with suggestions.
    """
    try:
        # Fetch messages from the resume refinement thread
        chat_messages = await fetch_thread_messages(state["thread_id"])

        if not chat_messages:
            logger.warning(f"No messages found in thread {state['thread_id']}")
            return {"suggestions": WorkExperienceEnhancementSuggestions()}

        # Initialize LLM with structured output
        llm = get_openrouter_model(ModelName.OPENAI__GPT_4O)
        llm_structured = llm.with_structured_output(WorkExperienceEnhancementSuggestions)

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", _SYSTEM_PROMPT),
                ("user", _USER_PROMPT),
                MessagesPlaceholder(variable_name="chat_history"),
            ]
        )

        # Build chain and invoke
        chain = prompt | llm_structured
        result = chain.invoke(
            {
                "work_experience": state["work_experience"],
                "chat_history": chat_messages,
            }
        )

        # Validate result
        if isinstance(result, dict):
            validated = WorkExperienceEnhancementSuggestions.model_validate(result)
        else:
            validated = result

        logger.info(
            f"Extracted experience updates: "
            f"role_overviews={len(validated.role_overviews)}, "
            f"company_overviews={len(validated.company_overviews)}, "
            f"skills={len(validated.skills)}, "
            f"achievements={len(validated.achievements)}"
        )

        return {"suggestions": validated}

    except Exception as exc:
        logger.exception(f"Experience extraction failed: {exc}")
        # Graceful degradation: return empty suggestions
        return {"suggestions": WorkExperienceEnhancementSuggestions()}


# ==================== Graph Definition ====================


def build_graph() -> StateGraph:
    """Build the experience extraction graph."""
    builder = StateGraph(ExperienceExtractionState)

    # Add the extraction node
    builder.add_node("extract", extract_experience_updates)

    # Define edges
    builder.add_edge(START, "extract")
    builder.add_edge("extract", END)

    return builder.compile()


# Compiled graph for LangGraph deployment
graph = build_graph()

