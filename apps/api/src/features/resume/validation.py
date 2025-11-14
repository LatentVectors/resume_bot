from __future__ import annotations


def validate_template_minimal(html_text: str) -> tuple[bool, list[str]]:
    """Validate minimal requirements for a resume Jinja2 HTML template.

    Performs lightweight checks inspired by the CLI helper to keep UX friendly:
    - Require `{{ name }}` and `{{ title }}` placeholders.
    - Require presence of at least one list section token hint (skills/experience/education/certifications).
    - Encourage `{% if %}` use for optional sections (warning only).

    Args:
        html_text: Raw HTML text of the template returned by the model.

    Returns:
        A tuple of (is_valid, warnings). If `is_valid` is False, rendering may still be attempted
        by the caller based on UX, but upstream should surface warnings.
    """
    warnings: list[str] = []
    is_valid = True

    required_placeholders = ["{{ name }}", "{{ title }}"]
    if not all(token in html_text for token in required_placeholders):
        is_valid = False
        warnings.append("Missing one or more required placeholders: {{ name }}, {{ title }}")

    # Heuristic for at least one list section placeholder
    if not any(token in html_text for token in ["skills", "experience", "education", "certifications"]):
        is_valid = False
        warnings.append("Template seems to lack list sections (skills/experience/education/certifications).")

    # Encourage conditional blocks but do not fail
    if "{% if" not in html_text:
        warnings.append(
            "No conditional sections detected. Ensure optional sections are wrapped in {% if ... %} blocks."
        )

    return is_valid, warnings


__all__ = ["validate_template_minimal"]
