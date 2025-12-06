"""OpenRouter model initialization utilities."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

from .model_names import ModelName


def get_openrouter_model(model: ModelName) -> ChatOpenAI:
    """Initialize a ChatOpenAI model using OpenRouter.

    Args:
        model: ModelName enum member specifying the model to use.

    Returns:
        ChatOpenAI instance configured for OpenRouter.
    """
    return ChatOpenAI(
        model=model.value,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", ""),
            "X-Title": os.getenv("OPENROUTER_X_TITLE", ""),
        },
    )

