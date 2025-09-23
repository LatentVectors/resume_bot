from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from openai import APIConnectionError
from pydantic import BaseModel, Field

from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

from ..state import GenerateNode, InternalState, PartialInternalState


def router_node(state: InternalState) -> PartialInternalState:
    """
    Decide which generator nodes to run based on the user's special instructions.

    Behavior:
    - Calls GPT-4o with structured output to select a list of generator targets
      from the enum: skills, experience, professional_summary.
    - If the model returns an empty list or an error occurs, default to running
      all generate nodes.

    Reads:
    - special_instructions: str | None

    Returns:
    - router_targets: list[GenerateNode]
    """
    logger.debug("NODE: router_node")

    special_instructions = state.special_instructions or ""

    try:
        response = chain.invoke({"special_instructions": special_instructions})
        validated = RouterOutput.model_validate(response)
        targets = validated.targets
    except Exception:
        # Fall back to all targets on error
        targets = [
            GenerateNode.skills,
            GenerateNode.experience,
            GenerateNode.professional_summary,
        ]

    # If the model returned no targets, run all
    if not targets:
        targets = [
            GenerateNode.skills,
            GenerateNode.experience,
            GenerateNode.professional_summary,
        ]

    return PartialInternalState(router_targets=targets)


# Prompt templates
system_prompt = """
You are a routing assistant for a resume generation system. Your task is to read the
<Special Instructions> from a user and decide which generators should run next.

You must choose zero or more from this fixed list of targets:
- skills
- experience
- professional_summary

Rules:
- If the user explicitly asks to update only one area (e.g., "only skills"), choose only that.
- If the user mentions multiple areas (e.g., "skills and summary"), include both.
- If instructions are empty or unclear, return ALL targets.
- Never include any value outside of the allowed list.
"""

user_prompt = """
<Special Instructions>
{special_instructions}
</Special Instructions>
"""


class RouterOutput(BaseModel):
    """Structured output for routing decisions."""

    targets: list[GenerateNode] = Field(
        description=(
            "A list of generator targets to run next. Values must be one or more of: "
            "skills, experience, professional_summary. Return an empty list only if no generation is needed."
        )
    )


llm = get_model(OpenAIModels.gpt_4o)
llm_structured = llm.with_structured_output(RouterOutput).with_retry(retry_if_exception_type=(APIConnectionError,))
chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    | llm_structured
)
