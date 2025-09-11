"""LangGraph workflow for resume generation."""

from loguru import logger

from src.agents.main import InputState, OutputState, main_agent


def generate_resume(user_input: str) -> str:
    """Generate a resume using the workflow."""
    logger.info(f"Running workflow with input: {user_input}")

    # Create initial state
    initial_state = InputState(user_input=user_input)

    # Run the workflow
    result = main_agent.invoke(initial_state)
    validated = OutputState.model_validate(result)

    logger.info(f"Workflow completed with response: {validated.response}")
    return validated.response
