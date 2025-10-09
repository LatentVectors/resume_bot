"""Shared formatting utilities for displaying data."""

from __future__ import annotations


def format_experience_with_achievements(experience, achievements: list) -> str:
    """Format a single experience with its achievements into a standardized string.

    Args:
        experience: Experience object with company_name, job_title, location,
                   start_date, end_date, company_overview, role_overview, skills.
        achievements: List of Achievement objects with id, title, and content.

    Returns:
        Formatted markdown string representation of the experience.
    """
    # Format dates
    start_str = experience.start_date.strftime("%b %Y")
    end_str = experience.end_date.strftime("%b %Y") if getattr(experience, "end_date", None) else "Present"

    # Build the header section
    lines = [
        f"# {experience.company_name}",
        f"ID: {experience.id}",
        f"Title: {experience.job_title}",
    ]

    # Add optional location
    location_val = getattr(experience, "location", None)
    if location_val:
        lines.append(f"Location: {location_val}")

    lines.append(f"Duration: {start_str} - {end_str}")
    lines.append("")  # Blank line

    # Add optional company overview
    company_overview = getattr(experience, "company_overview", None)
    if company_overview:
        lines.append("## Company Overview")
        lines.append(company_overview)
        lines.append("")

    # Add optional role overview
    role_overview = getattr(experience, "role_overview", None)
    if role_overview:
        lines.append("## Role Overview")
        lines.append(role_overview)
        lines.append("")

    # Add optional skills
    skills = getattr(experience, "skills", None) or []
    if skills:
        lines.append("## Skills")
        for skill in skills:
            lines.append(f"- {skill}")
        lines.append("")

    # Add achievements section
    if achievements:
        lines.append("## Achievements")
        lines.append("")
        for achievement in achievements:
            lines.append(f"### {achievement.title}")
            lines.append(f"ID: {achievement.id}")
            lines.append(achievement.content)
            lines.append("")

    return "\n".join(lines)


def format_all_experiences(experiences: list, achievements_by_exp: dict[int, list] | None = None) -> str:
    """Format all experiences into a single string with clear separation.

    Args:
        experiences: List of experience objects with company_name, job_title,
                    location, start_date, end_date attributes.
        achievements_by_exp: Optional dict mapping experience IDs to their achievements.

    Returns:
        Formatted string with all experiences separated by dividers.
    """
    if not experiences:
        return "No work experience available."

    formatted_sections = []
    for exp in experiences:
        achievements = achievements_by_exp.get(exp.id, []) if achievements_by_exp else []
        section = format_experience_with_achievements(exp, achievements)
        formatted_sections.append(section)

    div = "\n" + ("=" * 80) + "\n\n"
    return div.join(formatted_sections)
