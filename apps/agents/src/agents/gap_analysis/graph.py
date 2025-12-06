"""Gap analysis agent graph.

Analyzes the fit between job requirements and user experience,
identifying matched requirements, partial matches, gaps, and
suggested clarifying questions.
"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import TypedDict

from httpx import HTTPStatusError
from langgraph.graph import END, START, StateGraph
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field

from src.shared.llm import get_openrouter_model
from src.shared.model_names import ModelName
from src.shared.prompts import PromptName, load_prompt


logger = logging.getLogger(__name__)


# ==================== State Definitions ====================


class InputState(BaseModel):
    """Input state for gap analysis agent."""

    job_description: str = Field(description="The full text of the job description to analyze")
    work_experience: str = Field(description="Pre-formatted markdown string of work experience")


class OutputState(BaseModel):
    """Output state for gap analysis agent."""

    analysis: str = Field(default="", description="Markdown formatted gap analysis")


class InternalState(InputState, OutputState):
    """Internal state combining input and output for gap analysis agent."""

    pass


class PartialInternalState(TypedDict, total=False):
    """Partial internal state for node return types."""

    job_description: str
    work_experience: str
    analysis: str


# ==================== Node Enum ====================


class Node(StrEnum):
    """Node names for the gap analysis graph."""

    START = START
    ANALYZE = "analyze"
    END = END


# ==================== LLM Setup ====================


_prompt = load_prompt(PromptName.GAP_ANALYSIS)
_llm = get_openrouter_model(ModelName.OPENAI__GPT_4O)
_chain = _prompt | _llm | StrOutputParser()


# ==================== Nodes ====================


def analyze(state: InternalState) -> PartialInternalState:
    """Analyze the fit between job requirements and user experience.

    Args:
        state: The current internal state containing job description and work experience.

    Returns:
        Partial state with the analysis result.
    """
    try:
        if not state.job_description or not state.job_description.strip():
            logger.warning("Gap analysis called with empty job description")
            return {"analysis": ""}

        if not state.work_experience or not state.work_experience.strip():
            logger.warning("Gap analysis called with empty work experience")
            return {"analysis": ""}

        result = _chain.invoke({
            "job_description": state.job_description,
            "work_experience": state.work_experience,
        })

        if not result or not result.strip():
            logger.warning("Gap analysis returned empty result from LLM")
            return {"analysis": ""}

        return {"analysis": result}

    except HTTPStatusError as exc:
        if exc.response.status_code == 429:
            logger.error(f"Rate limit exceeded during gap analysis: {exc}")
            return {"analysis": ""}
        logger.exception(f"HTTP error during gap analysis: {exc}")
        return {"analysis": ""}
    except Exception as exc:
        logger.exception(
            f"Gap analysis failed. Job description length: {len(state.job_description) if state.job_description else 0}, "
            f"Work experience length: {len(state.work_experience) if state.work_experience else 0}, "
            f"Error: {exc}"
        )
        return {"analysis": ""}


# ==================== Graph Construction ====================


builder = StateGraph(
    InternalState,
    input=InputState,
    output=OutputState,
)

# === NODES ===
builder.add_node(Node.ANALYZE, analyze)

# === EDGES ===
builder.add_edge(Node.START, Node.ANALYZE)
builder.add_edge(Node.ANALYZE, Node.END)

# === GRAPH ===
graph = builder.compile()

