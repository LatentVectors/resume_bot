from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from openai import APIConnectionError
from pydantic import BaseModel

from app.constants import LLMTag
from src.core.models import OpenAIModels, get_model
from src.logging_config import logger


class TitleCompany(BaseModel):
    """Structured output for job title and company extraction."""

    title: str | None
    company: str | None


_SYSTEM_PROMPT = """
You extract the job title and company from arbitrary job-related text.
Return concise values without extra punctuation or qualifiers.
If either field cannot be determined, return it as null.
"""

_USER_PROMPT = """
Text:
{text}
"""


# Model and chain setup
_llm = get_model(OpenAIModels.gpt_4o_mini)
_llm_structured = _llm.with_structured_output(TitleCompany).with_retry(retry_if_exception_type=(APIConnectionError,))
_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("user", _USER_PROMPT),
        ]
    )
    | _llm_structured
)


def extract_title_company(text: str) -> TitleCompany:
    """Extract title and company from freeform text using an LLM.

    Returns TitleCompany with fields possibly None on failure or uncertainty.
    """
    try:
        config = RunnableConfig(
            tags=[LLMTag.JOB_EXTRACTION.value],
        )
        result = _chain.invoke({"text": text}, config=config)
        # Safety: model may return dict; validate to our schema
        if isinstance(result, dict):
            validated = TitleCompany.model_validate(result)
        else:
            validated = TitleCompany.model_validate(result)
        return validated
    except Exception as exc:  # Broad catch to satisfy spec: do not raise to UI
        logger.exception("Title/Company extraction failed: %s", exc)
        return TitleCompany(title=None, company=None)
