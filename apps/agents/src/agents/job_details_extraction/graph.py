"""Job details extraction agent graph.

Extracts job title and company name from job description text
using structured output.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TypedDict

from httpx import HTTPStatusError
from langgraph.graph import END, START, StateGraph
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.shared.llm import get_openrouter_model
from src.shared.models import TitleCompany


logger = logging.getLogger(__name__)


# ==================== State Definitions ====================


class InputState(BaseModel):
    """Input state for job details extraction agent."""

    job_description: str = Field(description="The job description text to extract details from")


class OutputState(BaseModel):
    """Output state for job details extraction agent."""

    title: str | None = Field(default=None, description="The extracted job title")
    company: str | None = Field(default=None, description="The extracted company name")


class InternalState(InputState, OutputState):
    """Internal state combining input and output for job details extraction agent."""

    pass


class PartialInternalState(TypedDict, total=False):
    """Partial internal state for node return types."""

    job_description: str
    title: str | None
    company: str | None


# ==================== Node Enum ====================


class Node(StrEnum):
    """Node names for the job details extraction graph."""

    START = START
    EXTRACT = "extract"
    END = END


# ==================== Prompt Templates ====================


_SYSTEM_PROMPT = """
You extract the job title and company from arbitrary job-related text.
Return concise values without extra punctuation or qualifiers.
If either field cannot be determined, return it as null.
"""

_USER_PROMPT = """
Text:
{job_description}
"""


# ==================== LLM Setup ====================


_llm = get_openrouter_model("openai/gpt-4o-mini")
_llm_structured = _llm.with_structured_output(TitleCompany)
_chain = (
    ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("user", _USER_PROMPT),
    ])
    | _llm_structured
)


# ==================== Nodes ====================


def extract(state: InternalState) -> PartialInternalState:
    """Extract job title and company from job description text.

    Args:
        state: The current internal state containing the job description.

    Returns:
        Partial state with extracted title and company (may be None).
    """
    try:
        if not state.job_description or not state.job_description.strip():
            logger.warning("Job details extraction called with empty job description")
            return {"title": None, "company": None}

        result = _chain.invoke({"job_description": state.job_description})

        # Handle both dict and TitleCompany responses
        if isinstance(result, dict):
            validated = TitleCompany.model_validate(result)
        else:
            validated = result

        return {"title": validated.title, "company": validated.company}

    except HTTPStatusError as exc:
        if exc.response.status_code == 429:
            logger.error(f"Rate limit exceeded during job details extraction: {exc}")
            return {"title": None, "company": None}
        logger.exception(f"HTTP error during job details extraction: {exc}")
        return {"title": None, "company": None}
    except Exception as exc:
        logger.exception(f"Job details extraction failed: {exc}")
        return {"title": None, "company": None}


# ==================== Graph Construction ====================


builder = StateGraph(
    InternalState,
    input=InputState,
    output=OutputState,
)

# === NODES ===
builder.add_node(Node.EXTRACT, extract)

# === EDGES ===
builder.add_edge(Node.START, Node.EXTRACT)
builder.add_edge(Node.EXTRACT, Node.END)

# === GRAPH ===
graph = builder.compile()

