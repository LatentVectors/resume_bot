"""Utilities for generating HTML diffs between text content."""

from __future__ import annotations

import difflib
from html import escape


def generate_diff_html(original: str, proposed: str) -> str:
    """Generate HTML diff showing additions and deletions.

    Uses difflib.SequenceMatcher.get_opcodes() to compare strings.
    Returns HTML with CSS classes for styling.

    Args:
        original: The existing content
        proposed: The proposed new content

    Returns:
        HTML string with styled spans:
        - <span class="diff-added">new text</span> for additions (green)
        - <span class="diff-deleted">old text</span> for deletions (red strikethrough)
        - Normal text for unchanged content
    """
    if original == proposed:
        return escape(original)

    matcher = difflib.SequenceMatcher(None, original, proposed)
    opcodes = matcher.get_opcodes()

    html_parts = []
    for tag, i1, i2, j1, j2 in opcodes:
        if tag == "equal":
            # Unchanged content - escape and add as-is
            html_parts.append(escape(original[i1:i2]))
        elif tag == "delete":
            # Content removed - wrap in diff-deleted span
            deleted_text = escape(original[i1:i2])
            html_parts.append(f'<span class="diff-deleted">{deleted_text}</span>')
        elif tag == "insert":
            # Content added - wrap in diff-added span
            added_text = escape(proposed[j1:j2])
            html_parts.append(f'<span class="diff-added">{added_text}</span>')
        elif tag == "replace":
            # Content replaced - show deletion then addition
            deleted_text = escape(original[i1:i2])
            added_text = escape(proposed[j1:j2])
            html_parts.append(f'<span class="diff-deleted">{deleted_text}</span>')
            html_parts.append(f'<span class="diff-added">{added_text}</span>')

    return "".join(html_parts)

