from __future__ import annotations

from datetime import datetime


def sanitize_for_filename(value: str) -> str:
    """Return a filesystem-safe fragment for use in a filename.

    Args:
        value: Arbitrary string to be used as part of a filename

    Returns:
        A cleaned string with disallowed characters replaced and whitespace collapsed
    """
    cleaned = (
        (value or "")
        .strip()
        .replace("/", "-")
        .replace("\\", "-")
        .replace(":", "-")
        .replace("*", "-")
        .replace("?", "-")
        .replace('"', "'")
        .replace("<", "-")
        .replace(">", "-")
        .replace("|", "-")
    )
    return " ".join(cleaned.split())


def build_resume_download_filename(
    company_name: str | None,
    job_title: str | None,
    full_name: str,
    as_of: datetime | None = None,
) -> str:
    """Build a standardized resume download filename.

    Format: "Resume - {company_name} - {job_title} - {full_name} - {yyyy_mm_dd}.pdf"

    Args:
        company_name: Company name or None
        job_title: Job title or None
        full_name: User's full name
        as_of: Optional date to use; defaults to now

    Returns:
        A filename string ending in .pdf
    """
    dt = as_of or datetime.now()
    date_str = dt.strftime("%Y_%m_%d")
    company = sanitize_for_filename(company_name or "Unknown Company")
    title = sanitize_for_filename(job_title or "Unknown Title")
    name = sanitize_for_filename(full_name or "Unknown Name")
    return f"Resume - {company} - {title} - {name} - {date_str}.pdf"
