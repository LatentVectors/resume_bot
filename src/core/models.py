from enum import Enum

from langchain.chat_models import init_chat_model
from langchain.chat_models.base import BaseChatModel

from src.config import settings as SETTINGS
from src.logging_config import logger

OPENAI_PREFIX = "openai:"


class OpenAIModels(Enum):
    gpt_4o_mini = f"{OPENAI_PREFIX}gpt-4o-mini"
    """GPT-4o Mini"""
    gpt_4o = f"{OPENAI_PREFIX}gpt-4o"
    """GPT-4o"""
    gpt_3_5_turbo = f"{OPENAI_PREFIX}gpt-3.5-turbo"
    """GPT-3.5 Turbo"""
    gpt_5 = f"{OPENAI_PREFIX}gpt-5"
    """GPT-5"""


ModelName = OpenAIModels

_models: dict[ModelName, BaseChatModel] = {}


def get_model(model: ModelName, max_retries: int = 2) -> BaseChatModel:
    """Get a model by name.

    Args:
        model: The model to get.
        max_retries: Maximum number of retries for the model.

    Returns:
        A singleton instance of the model.
    """
    api_key = None
    if model.value.startswith(OPENAI_PREFIX):
        api_key = SETTINGS.openai_api_key
        if api_key is None:
            logger.error("OpenAI API key is not set")
            raise ValueError("OpenAI API key is not set")

    if model not in _models:
        _models[model] = init_chat_model(
            model.value,
            max_retries=max_retries,
            api_key=api_key,
        )
    return _models[model]
