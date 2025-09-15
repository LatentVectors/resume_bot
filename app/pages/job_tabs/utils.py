from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from src.config import settings


def fmt_datetime(dt: datetime | None) -> str:
    """Format a datetime for display.

    Args:
        dt: The datetime to format.

    Returns:
        A human-readable string representation or an em dash if missing.
    """
    if not dt:
        return "—"
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:  # pragma: no cover - defensive fallback
        return str(dt)


def badge(has_content: bool) -> str:
    """Return a Material icon token indicating content presence.

    Args:
        has_content: Whether the content exists.

    Returns:
        A Material icon token indicating content presence.
    """
    return ":material/radio_button_checked:" if has_content else ":material/radio_button_unchecked:"


def resume_exists(filename: str | None) -> bool:
    """Check if a resume PDF exists by filename under the data directory.

    Args:
        filename: The resume file name stored for the job.

    Returns:
        True if the resolved file exists, otherwise False.
    """
    if not filename:
        return False
    try:
        pdf_path = (settings.data_dir / "resumes" / filename).resolve()
        return pdf_path.exists()
    except Exception:  # pragma: no cover - defensive fallback
        return False


@runtime_checkable
class SupportsJob(Protocol):
    """Structural type for Job objects used by tab renderers."""

    id: int
    status: str

    # Optional text fields
    job_title: str | None
    company_name: str | None
    job_description: str | None

    # Timestamps
    created_at: datetime | None
    applied_at: datetime | None

    # Flags and filenames
    is_favorite: bool | None
    has_resume: bool | None
    has_cover_letter: bool | None
    resume_filename: str | None
