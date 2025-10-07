from __future__ import annotations

import base64
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from openai import APIConnectionError

from src.core.models import OpenAIModels, get_model
from src.features.cover_letter.prompt import cover_letter_template_prompt


def _to_image_content_part(image: bytes | str) -> dict[str, Any]:
    """Build a LangChain/OpenAI multimodal image content part from bytes or a URL/data URL string.

    Defaults to PNG when bytes are provided.

    Args:
        image: Image as raw bytes or URL/data URL string.

    Returns:
        Dictionary with image content part for multimodal message.
    """
    if isinstance(image, bytes):
        data_url = "data:image/png;base64," + base64.b64encode(image).decode("utf-8")
        return {"type": "image_url", "image_url": {"url": data_url}}
    # Assume provided string is already a valid URL or data URL
    return {"type": "image_url", "image_url": {"url": image}}


def _clean_html_output(raw_text: str) -> str:
    """Remove markdown code fences/backticks and trim whitespace.

    Args:
        raw_text: Raw output from LLM.

    Returns:
        Cleaned HTML string without markdown fences.
    """
    if not raw_text:
        return ""

    # Prefer extracting content inside a fenced block if present
    fenced_match = re.search(r"```(?:html)?\s*([\s\S]*?)\s*```", raw_text, flags=re.IGNORECASE)
    if fenced_match:
        cleaned = fenced_match.group(1)
    else:
        # Strip stray triple backticks or single backticks
        cleaned = raw_text.replace("```", "").replace("`", "")
    return cleaned.strip()


def _normalize_jinja_braces(text: str) -> str:
    """Normalize over-escaped Jinja braces from LLM output.

    Some upstream escaping or examples in prompts can cause the model to emit
    tokens like ``{{{{ name }}}}`` instead of ``{{ name }}``. This function
    reduces quadruple braces to standard Jinja double braces while leaving other
    content intact.

    Args:
        text: HTML text with potentially over-escaped Jinja braces.

    Returns:
        Normalized HTML text with standard Jinja2 braces.
    """
    if not text:
        return ""
    return text.replace("{{{{", "{{").replace("}}}}", "}}")


def generate_cover_letter_template_html(
    user_text: str,
    current_html: str | None,
    image: bytes | None,
) -> str:
    """Generate or edit a cover letter HTML template via LLM.

    Args:
        user_text: The user's instruction or feedback for the template.
        current_html: The currently selected template HTML (if editing), otherwise None.
        image: Optional image as raw bytes (PNG assumed).

    Returns:
        Clean raw HTML string for the cover letter template (no markdown fences).

    Raises:
        ValueError: If LLM returns empty HTML.
        RuntimeError: If template rendering fails.
    """
    # Compose the user content parts (text + optional image)
    if current_html:
        text_directive = (
            "Revise the provided HTML cover letter template per the user's instructions. "
            "Return ONLY the complete raw HTML with no explanations, no markdown, and no code fences.\n\n"
            "User instructions:\n" + (user_text or "") + "\n\n"
            "Current template HTML follows. Replace it completely with the updated full HTML.\n"
            "<CURRENT_TEMPLATE_START>\n" + current_html + "\n<CURRENT_TEMPLATE_END>\n"
        )
    else:
        text_directive = (
            "Generate a complete professional cover letter template as raw HTML. "
            "Return ONLY the complete raw HTML with no explanations, no markdown, and no code fences.\n\n"
            "User instructions:\n" + (user_text or "")
        )

    user_parts: list[dict[str, Any]] = [{"type": "text", "text": text_directive}]
    if image is not None:
        try:
            user_parts.append(_to_image_content_part(image))
        except Exception:
            # If image handling fails, fall back to text-only
            pass

    # Model setup (prefer GPT-5)
    llm = get_model(OpenAIModels.gpt_5)
    llm_with_retry = llm.with_retry(retry_if_exception_type=(APIConnectionError,))

    # Send the system prompt as-is so examples show correct Jinja ``{{ }}`` syntax.
    system_text = cover_letter_template_prompt

    messages = [
        SystemMessage(content=system_text),
        HumanMessage(content=user_parts),
    ]

    ai_message = llm_with_retry.invoke(messages)
    raw_text = getattr(ai_message, "content", str(ai_message))
    cleaned = _clean_html_output(raw_text)
    normalized = _normalize_jinja_braces(cleaned)

    if not normalized.strip():
        raise ValueError("Model returned empty cover letter template HTML")

    return normalized
