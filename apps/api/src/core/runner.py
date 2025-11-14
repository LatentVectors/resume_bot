from __future__ import annotations

from typing import Any

from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from src.core.context import AgentContext
from src.core.hitl import INTERRUPT_KEY, handle_interrupts
from src.logging_config import logger


def stream_agent(
    graph: CompiledStateGraph[Any, Any, Any, Any],
    input_state: Any,
    config: RunnableConfig,
    *,
    context: AgentContext,
) -> CompiledStateGraph[Any, Any, Any, Any]:
    """Stream execution of a compiled LangGraph agent until completion.

    This is a generic streaming runner that can be reused for any compiled
    LangGraph agent. It handles interactive interrupts and resumes execution
    until the graph completes.

    Args:
        graph: The compiled graph to execute.
        input_state: The initial input state for the graph.
        config: Runnable configuration passed to the graph.
        context: Runtime context propagated through graph execution.

    Returns:
        The same compiled graph instance, which will contain the final state
        retrievable via `get_state(config=...)`.
    """

    logger.info("Starting agent...")
    current_input: object = input_state
    while True:
        stream = graph.stream(current_input, context=context, config=config)  # type: ignore[arg-type]
        interrupted: bool = False
        for event in stream:
            logger.info("--> Event Batch <--")
            for key in event.keys():
                logger.info(f"EVENT: {key}")
            interrupts = event.get(INTERRUPT_KEY, None)
            if interrupts:
                logger.info("Interrupts:")
                commands = handle_interrupts(interrupts)
                current_input = Command(resume=commands)
                interrupted = True
                break
        if not interrupted:
            break
    return graph


