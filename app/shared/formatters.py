"""Shared formatting utilities for displaying data."""

from __future__ import annotations


def format_all_experiences(experiences: list) -> str:
    """Format all experiences into a single string with clear separation.

    Args:
        experiences: List of experience objects with company_name, job_title,
                    location, start_date, end_date, and content attributes.

    Returns:
        Formatted string with all experiences separated by dividers.
    """
    if not experiences:
        return "No work experience available."

    formatted_sections = []
    for exp in experiences:
        # Format dates
        start_str = exp.start_date.strftime("%b %Y")
        end_str = exp.end_date.strftime("%b %Y") if getattr(exp, "end_date", None) else "Present"

        # Build the section with explicit labels
        section = f"# {exp.company_name}\n"
        section += f"Title: {exp.job_title}\n"

        location_val = getattr(exp, "location", None)
        if location_val:
            section += f"Location: {location_val}\n"

        section += f"Duration: {start_str} - {end_str}\n"

        content = getattr(exp, "content", "")
        if content:
            section += f"\n{content}\n"

        formatted_sections.append(section)

    div = "\n" + ("=" * 80) + "\n\n"
    return div.join(formatted_sections)
