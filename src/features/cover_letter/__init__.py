"""Cover letter feature module."""

from .content import DUMMY_COVER_LETTER_DATA
from .llm_template import generate_cover_letter_template_html
from .types import CoverLetterData
from .utils import convert_html_to_pdf, list_available_templates, render_template_to_html
from .validation import validate_template_minimal

__all__ = [
    "CoverLetterData",
    "DUMMY_COVER_LETTER_DATA",
    "generate_cover_letter_template_html",
    "validate_template_minimal",
    "list_available_templates",
    "convert_html_to_pdf",
    "render_template_to_html",
]
