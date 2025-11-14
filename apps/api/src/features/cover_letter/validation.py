from __future__ import annotations


def validate_template_minimal(html_text: str) -> tuple[bool, list[str]]:
    """Validate minimal requirements for a cover letter Jinja2 HTML template.

    Checks for required Jinja2 variables and common template elements:
    - Required: {{ name }}, {{ email }}, date variable (can be {{ date }} or {{ date.strftime(...) }})
    - Required: At least one use of body_paragraphs (e.g., {% for paragraph in body_paragraphs %})
    - Optional (no warning): {{ phone }}, {{ title }}

    Args:
        html_text: Raw HTML text of the template.

    Returns:
        A tuple of (is_valid, warnings). If `is_valid` is False, the template is missing
        critical placeholders. Warnings provide feedback on what is missing.
    """
    warnings: list[str] = []
    is_valid = True

    # Required placeholders - check for basic presence
    if "{{ name }}" not in html_text:
        is_valid = False
        warnings.append("Missing required placeholder: {{ name }}")

    if "{{ email }}" not in html_text:
        is_valid = False
        warnings.append("Missing required placeholder: {{ email }}")

    # Check for date usage (can be {{ date }} or {{ date.strftime(...) }})
    if "{{ date" not in html_text:
        is_valid = False
        warnings.append("Missing required placeholder: {{ date }} (or date.strftime(...))")

    # Check for body_paragraphs usage (for loop or direct reference)
    if "body_paragraphs" not in html_text:
        is_valid = False
        warnings.append("Template must include body_paragraphs (e.g., {% for paragraph in body_paragraphs %})")

    return is_valid, warnings


__all__ = ["validate_template_minimal"]
