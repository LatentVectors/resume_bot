"""OpenRouter model initialization utilities."""

from __future__ import annotations

import os

from langchain_openai import ChatOpenAI


def get_openrouter_model(model_id: str) -> ChatOpenAI:
    """Initialize a ChatOpenAI model using OpenRouter.

    Args:
        model_id: OpenRouter model identifier (e.g., 'google/gemini-2.5-pro', 'openai/gpt-4o')

    Returns:
        ChatOpenAI instance configured for OpenRouter.
    """
    return ChatOpenAI(
        model=model_id,
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        default_headers={
            "HTTP-Referer": os.getenv("OPENROUTER_HTTP_REFERER", ""),
            "X-Title": os.getenv("OPENROUTER_X_TITLE", ""),
        },
    )

