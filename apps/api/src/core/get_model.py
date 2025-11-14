"""Model retrieval with singleton pattern."""

from __future__ import annotations

from langchain.chat_models.base import BaseChatModel
from langchain_openai import ChatOpenAI

from src.config import settings
from src.core.models import ModelName

_models: dict[ModelName, BaseChatModel] = {}


def get_model(model: ModelName, max_retries: int = 2) -> BaseChatModel:
    """Get a model by name through OpenRouter.

    Args:
        model: The model to get from OpenRouter.
        max_retries: Maximum number of retries for the model.

    Returns:
        A singleton instance of the model.
    """
    if model not in _models:
        # Prepare default headers for attribution
        default_headers = {}
        if settings.openrouter_site_url and settings.openrouter_site_name:
            default_headers["HTTP-Referer"] = settings.openrouter_site_url
            default_headers["X-Title"] = settings.openrouter_site_name

        _models[model] = ChatOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            model=model.value,
            max_retries=max_retries,
            default_headers=default_headers if default_headers else None,
        )
    return _models[model]

