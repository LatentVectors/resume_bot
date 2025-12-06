"""Data fetching utilities for resume refinement agent.

Contains functions for fetching user profiles, experiences, achievements,
jobs, and intake sessions from the API.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


def get_api_base() -> str:
    """Get the API base URL from environment."""
    return os.getenv("API_BASE_URL", "http://localhost:3000")


# ==================== User Profile ====================


def fetch_user_profile(api_base: str, user_id: int) -> dict | None:
    """Fetch user profile data from the API.

    Args:
        api_base: Base URL for the API.
        user_id: ID of the user to fetch.

    Returns:
        User profile dict or None if not found.
    """
    try:
        response = httpx.get(f"{api_base}/api/users/{user_id}", timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Failed to fetch user profile {user_id}: HTTP {exc.response.status_code}")
        return None
    except Exception as exc:
        logger.warning(f"Error fetching user profile {user_id}: {exc}")
        return None


# ==================== Experiences ====================


def fetch_experience(api_base: str, experience_id: int) -> dict | None:
    """Fetch experience data from the API.

    Args:
        api_base: Base URL for the API.
        experience_id: ID of the experience to fetch.

    Returns:
        Experience dict or None if not found.
    """
    try:
        response = httpx.get(f"{api_base}/api/experiences/{experience_id}", timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Failed to fetch experience {experience_id}: HTTP {exc.response.status_code}")
        return None
    except Exception as exc:
        logger.warning(f"Error fetching experience {experience_id}: {exc}")
        return None


def fetch_user_experiences(api_base: str, user_id: int) -> list[dict]:
    """Fetch all experiences for a user from the API.

    Args:
        api_base: Base URL for the API.
        user_id: ID of the user to fetch experiences for.

    Returns:
        List of experience dicts, or empty list if error.
    """
    try:
        response = httpx.get(
            f"{api_base}/api/experiences",
            params={"user_id": user_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Failed to fetch experiences for user {user_id}: HTTP {exc.response.status_code}")
        return []
    except Exception as exc:
        logger.warning(f"Error fetching experiences for user {user_id}: {exc}")
        return []


# ==================== Achievements ====================


def fetch_achievements(api_base: str, experience_id: int) -> list[dict]:
    """Fetch all achievements for an experience from the API.

    Args:
        api_base: Base URL for the API.
        experience_id: ID of the experience to fetch achievements for.

    Returns:
        List of achievement dicts, or empty list if error.
    """
    try:
        response = httpx.get(
            f"{api_base}/api/achievements",
            params={"experience_id": experience_id},
            timeout=10.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(
            f"Failed to fetch achievements for experience {experience_id}: HTTP {exc.response.status_code}"
        )
        return []
    except Exception as exc:
        logger.warning(f"Error fetching achievements for experience {experience_id}: {exc}")
        return []


# ==================== Jobs ====================


def fetch_job(api_base: str, job_id: int) -> dict | None:
    """Fetch job data from the API.

    Args:
        api_base: Base URL for the API.
        job_id: ID of the job to fetch.

    Returns:
        Job dict or None if not found.
    """
    try:
        response = httpx.get(f"{api_base}/api/jobs/{job_id}", timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Failed to fetch job {job_id}: HTTP {exc.response.status_code}")
        return None
    except Exception as exc:
        logger.warning(f"Error fetching job {job_id}: {exc}")
        return None


def fetch_intake_session(api_base: str, job_id: int) -> dict | None:
    """Fetch intake session data from the API.

    Args:
        api_base: Base URL for the API.
        job_id: ID of the job to fetch intake session for.

    Returns:
        Intake session dict or None if not found.
    """
    try:
        response = httpx.get(f"{api_base}/api/jobs/{job_id}/intake-session", timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Failed to fetch intake session for job {job_id}: HTTP {exc.response.status_code}")
        return None
    except Exception as exc:
        logger.warning(f"Error fetching intake session for job {job_id}: {exc}")
        return None


# ==================== Formatting Helpers ====================


def format_date(date_str: str | None) -> str:
    """Format a date string to 'Mon YYYY' format.

    Args:
        date_str: ISO date string or None.

    Returns:
        Formatted date string or 'Present' if None.
    """
    if not date_str:
        return "Present"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%b %Y")
    except (ValueError, AttributeError):
        return date_str


def format_experience_with_achievements(experience: dict, achievements: list[dict]) -> str:
    """Format a single experience with its achievements into a standardized string.

    Args:
        experience: Experience dict from the API.
        achievements: List of achievement dicts from the API.

    Returns:
        Formatted markdown string representation of the experience.
    """
    start_str = format_date(experience.get("start_date"))
    end_str = format_date(experience.get("end_date"))

    lines = [
        f"# {experience.get('company_name', 'Unknown Company')}",
        f"ID: {experience.get('id', 'N/A')}",
        f"Title: {experience.get('job_title', 'N/A')}",
    ]

    location = experience.get("location")
    if location:
        lines.append(f"Location: {location}")

    lines.append(f"Duration: {start_str} - {end_str}")
    lines.append("")

    company_overview = experience.get("company_overview")
    if company_overview:
        lines.append("## Company Overview")
        lines.append(company_overview)
        lines.append("")

    role_overview = experience.get("role_overview")
    if role_overview:
        lines.append("## Role Overview")
        lines.append(role_overview)
        lines.append("")

    skills = experience.get("skills") or []
    if skills and isinstance(skills, list):
        lines.append("## Skills")
        for skill in skills:
            lines.append(f"- {skill}")
        lines.append("")

    if achievements:
        lines.append("## Achievements")
        lines.append("")
        for achievement in achievements:
            lines.append(f"### {achievement.get('title', 'Untitled')}")
            lines.append(f"ID: {achievement.get('id', 'N/A')}")
            lines.append(achievement.get("content", ""))
            lines.append("")

    return "\n".join(lines)


# ==================== High-Level Data Fetching ====================


def fetch_formatted_work_experience(user_id: int) -> str:
    """Fetch and format all work experiences for a user.

    This function fetches all experiences and their achievements from the API
    and formats them into a standardized markdown string that includes all
    database IDs for reference.

    Args:
        user_id: ID of the user to fetch work experience for.

    Returns:
        Formatted markdown string with all work experiences and achievements.
    """
    api_base = get_api_base()

    # Fetch all experiences for the user
    experiences = fetch_user_experiences(api_base, user_id)

    if not experiences:
        return "No work experience available."

    # Fetch achievements for each experience
    achievements_by_exp: dict[int, list[dict]] = {}
    for exp in experiences:
        exp_id = exp.get("id")
        if exp_id:
            achievements_by_exp[exp_id] = fetch_achievements(api_base, exp_id)

    # Format all experiences
    formatted_sections = []
    for exp in experiences:
        exp_id = exp.get("id")
        achievements = achievements_by_exp.get(exp_id, []) if exp_id else []
        section = format_experience_with_achievements(exp, achievements)
        formatted_sections.append(section)

    divider = "\n" + ("=" * 80) + "\n\n"
    return divider.join(formatted_sections)


@dataclass
class JobContext:
    """Container for job-related context data fetched from the API."""

    job_description: str
    gap_analysis: str
    stakeholder_analysis: str


def fetch_job_context(job_id: int) -> JobContext:
    """Fetch job description, gap analysis, and stakeholder analysis from the API.

    Args:
        job_id: ID of the job to fetch context for.

    Returns:
        JobContext with fetched data (empty strings if fetch fails).
    """
    api_base = get_api_base()

    # Fetch job data for job_description
    job_data = fetch_job(api_base, job_id)
    job_description = job_data.get("job_description", "") if job_data else ""

    # Fetch intake session for gap_analysis and stakeholder_analysis
    intake_session = fetch_intake_session(api_base, job_id)

    gap_analysis = ""
    stakeholder_analysis = ""

    if intake_session:
        # Handle potential JSON-encoded strings
        raw_gap = intake_session.get("gap_analysis", "")
        raw_stakeholder = intake_session.get("stakeholder_analysis", "")

        if raw_gap:
            try:
                parsed = json.loads(raw_gap)
                gap_analysis = parsed if isinstance(parsed, str) else raw_gap
            except (json.JSONDecodeError, TypeError):
                gap_analysis = raw_gap

        if raw_stakeholder:
            try:
                parsed = json.loads(raw_stakeholder)
                stakeholder_analysis = parsed if isinstance(parsed, str) else raw_stakeholder
            except (json.JSONDecodeError, TypeError):
                stakeholder_analysis = raw_stakeholder

    logger.info(
        f"Fetched job context for job {job_id}: "
        f"job_description={len(job_description)} chars, "
        f"gap_analysis={len(gap_analysis)} chars, "
        f"stakeholder_analysis={len(stakeholder_analysis)} chars"
    )

    return JobContext(
        job_description=job_description,
        gap_analysis=gap_analysis,
        stakeholder_analysis=stakeholder_analysis,
    )
