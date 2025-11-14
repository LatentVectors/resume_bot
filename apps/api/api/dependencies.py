"""Dependency injection for FastAPI routes."""

from __future__ import annotations

from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from src.database import db_manager


def get_session() -> Generator[Session, None, None]:
    """Dependency for database session.

    Yields:
        Database session that is automatically closed after the request.
    """
    with db_manager.get_session() as session:
        yield session


# Type alias for dependency injection
DBSession = Annotated[Session, Depends(get_session)]

