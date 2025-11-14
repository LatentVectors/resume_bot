from __future__ import annotations

from urllib.parse import urljoin

from src.config import settings


def build_app_url(path_with_query: str) -> str:
    """Build absolute URL from app base and a path like "/job?job_id=123".

    Args:
        path_with_query: Path beginning with "/", optionally containing a query string.

    Returns:
        Fully-qualified URL string.
    """
    base = settings.app_base_url.rstrip("/") + "/"
    relative = path_with_query.lstrip("/")
    return urljoin(base, relative)
