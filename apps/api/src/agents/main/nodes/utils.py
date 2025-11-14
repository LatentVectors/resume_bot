"""Utility functions for resume generation nodes."""

from __future__ import annotations

from ..state import Experience


def format_experiences_for_prompt(experiences: list[Experience]) -> str:
    """Format a list of experience objects into a string for use in prompt templates.

    Args:
        experiences: List of experience objects to format

    Returns:
        Formatted string representation of experiences
    """
    if not experiences:
        return "No work experience provided."

    formatted_experiences = []
    for exp in experiences:
        # Format dates
        start_date_str = exp.start_date.strftime("%B %Y")
        end_date_str = exp.end_date.strftime("%B %Y") if exp.end_date else "Present"
        date_range = f"{start_date_str} - {end_date_str}"

        # Format experience entry
        experience_text = f"""ID: {exp.id}
Company: {exp.company}
Title: {exp.title}
Duration: {date_range}
Description: {exp.content}"""

        if exp.points:
            experience_text += "\nKey Points:\n" + "\n".join(f"- {point}" for point in exp.points)

        formatted_experiences.append(experience_text)

    return "\n\n".join(formatted_experiences)
