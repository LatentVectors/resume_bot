"""Conversation summary workflow for Step 2→3 transition.

Summarizes the experience enhancement conversation to provide context
for resume generation.
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.constants import LLMTag
from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

# ==================== Main Workflow Function ====================


def summarize_conversation(messages: list[BaseMessage]) -> str:
    """Summarize the Step 2 conversation.

    Args:
        messages: Chat message history from stage 2.

    Returns:
        Summary string.
    """
    if not messages:
        return "No conversation to summarize."

    try:
        # Filter out any system messages from the input
        filtered_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]

        if not filtered_messages:
            return "No conversation to summarize."

        # Add user message requesting summary
        summary_request = HumanMessage(content="Provide a concise summary of key insights from this conversation.")
        messages_for_llm = filtered_messages + [summary_request]

        config = RunnableConfig(tags=[LLMTag.INTAKE_CONVERSATION_SUMMARY.value])
        response = _chain.invoke({"messages": messages_for_llm}, config=config)

        return response

    except Exception as exc:
        logger.exception("Error summarizing conversation: %s", exc)
        return "Unable to generate conversation summary."


# ==================== System Prompt ====================

_SYSTEM_PROMPT = """You are an expert career coach summarizing a conversation about a candidate's experience.

Extract key insights from the conversation, focusing on:
- Additional context provided beyond the written experience records
- Unique details, motivations, and interests expressed
- The candidate's fit assessment based on gap analysis and responses
- Clarifications or nuances that refine understanding of their background

Provide a concise summary in 2-4 paragraphs that will help tailor their resume to the job.
"""

# ==================== Chain Definition ====================

_llm = get_model(OpenAIModels.gpt_4o)
_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("placeholder", "{messages}"),
        ]
    )
    | _llm
    | StrOutputParser()
)
