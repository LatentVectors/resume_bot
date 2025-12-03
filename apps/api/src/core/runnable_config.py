"""Utility for creating RunnableConfig with LangSmith-compliant run IDs."""

from __future__ import annotations

from uuid import UUID

from langchain_core.runnables import RunnableConfig

try:
    from langsmith import uuid7
except ImportError:
    # Fallback to uuid4 if langsmith is not available
    import uuid

    def uuid7() -> UUID:  # type: ignore[misc]
        """Fallback to uuid4 if langsmith uuid7 is not available."""
        return uuid.uuid4()


def create_runnable_config(
    tags: list[str] | None = None,
    metadata: dict[str, object] | None = None,
    configurable: dict[str, object] | None = None,
    run_id: UUID | None = None,
) -> RunnableConfig:
    """Create a RunnableConfig with a LangSmith-compliant UUID v7 run ID.

    Args:
        tags: List of tags to attach to the run.
        metadata: Dictionary of metadata to attach to the run.
        configurable: Dictionary of configurable parameters.
        run_id: Optional custom run ID (UUID object). If not provided, generates a UUID v7.

    Returns:
        RunnableConfig instance with run_id set to UUID v7.
    """
    config_dict: dict[str, object] = {}

    if tags:
        config_dict["tags"] = tags

    if metadata:
        config_dict["metadata"] = metadata

    if configurable:
        config_dict["configurable"] = configurable

    # Set run_id to UUID v7 to comply with LangSmith requirements
    # LangSmith requires a UUID object (with .version attribute), not a string
    if run_id is None:
        run_id = uuid7()

    config_dict["run_id"] = run_id

    return RunnableConfig(**config_dict)

