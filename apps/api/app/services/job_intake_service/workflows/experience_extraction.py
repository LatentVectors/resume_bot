"""Experience extraction workflow for Step 3 of job intake.

Analyzes Step 2 conversation to extract suggested updates to user's work experiences.
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from openai import RateLimitError
from pydantic import BaseModel, Field

from app.constants import LLMTag
from app.exceptions import OpenAIQuotaExceededError
from app.shared.formatters import format_all_experiences
from src.core import ModelName, get_model
from src.database import (
    AchievementAdd,
    AchievementUpdate,
    CompanyOverviewUpdate,
    Experience,
    RoleOverviewUpdate,
    SkillAdd,
    db_manager,
)
from src.logging_config import logger

# ==================== Main Workflow Function ====================


def extract_experience_updates(
    chat_messages: list[HumanMessage | AIMessage],
    experiences: list[Experience],
) -> WorkExperienceEnhancementSuggestions:
    """Extract experience update suggestions from Step 2 conversation.

    Analyzes the complete Step 2 conversation (both user and AI messages) against
    all of the user's current work experiences to identify potential updates.

    Args:
        chat_messages: Complete Step 2 chat message history (user and AI messages)
        experiences: All user work experiences with achievements, skills, and overviews

    Returns:
        WorkExperienceEnhancementSuggestions Pydantic model instance with validated
        structured output containing proposed updates.

    Raises:
        OpenAIQuotaExceededError: If OpenAI API quota is exceeded.
    """
    try:
        # Format work experience for analysis
        achievements_by_exp: dict[int, list] = {}
        for exp in experiences:
            achievements = db_manager.list_experience_achievements(exp.id)
            achievements_by_exp[exp.id] = achievements

        work_experience = format_all_experiences(experiences, achievements_by_exp)

        # Configure LLM call
        config = RunnableConfig(
            tags=[LLMTag.EXPERIENCE_EXTRACTION.value],
        )

        # Invoke chain with inputs - chat_messages are passed directly as MessagesPlaceholder
        result = _chain.invoke(
            {
                "work_experience": work_experience,
                "chat_history": chat_messages,
            },
            config=config,
        )

        # Validate result is a Pydantic model instance
        if isinstance(result, dict):
            validated = WorkExperienceEnhancementSuggestions.model_validate(result)
        else:
            validated = result

        logger.info(
            "Extracted experience updates",
            extra={
                "role_overviews_count": len(validated.role_overviews),
                "company_overviews_count": len(validated.company_overviews),
                "skills_count": len(validated.skills),
                "achievements_count": len(validated.achievements),
            },
        )

        return validated

    except RateLimitError as exc:
        # Check if this is specifically a quota exceeded error
        error_message = str(exc)
        if "insufficient_quota" in error_message or "exceeded your current quota" in error_message:
            logger.error("OpenAI API quota exceeded during experience extraction: %s", exc)
            raise OpenAIQuotaExceededError() from exc
        # Re-raise other rate limit errors as generic exceptions
        logger.exception("OpenAI rate limit error during experience extraction: %s", exc)
        raise
    except Exception as exc:
        logger.exception(
            "Experience extraction failed with exception. Experience count: %d, Message count: %d, Error: %s",
            len(experiences) if experiences else 0,
            len(chat_messages) if chat_messages else 0,
            exc,
        )
        raise


# ==================== System Prompt (Placeholder) ====================

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

# ==================== Pydantic Models for Structured Output ====================
# Note: Proposal content models (RoleOverviewUpdate, CompanyOverviewUpdate, SkillAdd,
# AchievementAdd, AchievementUpdate) are imported from src.database as the canonical source.


class WorkExperienceEnhancementSuggestions(BaseModel):
    """Structured output schema for experience enhancement suggestions.

    Matches the schema defined in prompts/extract_experience_updates.json.
    """

    role_overviews: list[RoleOverviewUpdate] = Field(
        default_factory=list, description="A list of suggestions for updating role overviews"
    )
    company_overviews: list[CompanyOverviewUpdate] = Field(
        default_factory=list, description="A list of suggestions for updating company overviews"
    )
    skills: list[SkillAdd] = Field(default_factory=list, description="A list of suggestions for adding new skills")
    achievements: list[AchievementAdd | AchievementUpdate] = Field(
        default_factory=list, description="A list of suggestions for adding or updating achievements"
    )


# ==================== Model and Chain Setup ====================

_llm = get_model(ModelName.OPENAI__GPT_4O)
_llm_structured = _llm.with_structured_output(WorkExperienceEnhancementSuggestions)
_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        ("user", _USER_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
    ]
)
_chain = _prompt | _llm_structured
