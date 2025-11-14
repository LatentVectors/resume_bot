"""Pytest configuration and fixtures for API tests."""

import shutil
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlmodel import Session

from api.dependencies import get_session
from api.main import app
from src.config import settings
from src.database import DatabaseManager


@pytest.fixture(scope="session")
def test_database_path(tmp_path_factory):
    """Copy production database to test location."""
    prod_db_path = Path(settings.database_url.replace("sqlite:///", ""))

    # Create test database path
    test_db_path = tmp_path_factory.mktemp("test_data") / "test_resume_bot.db"

    if prod_db_path.exists():
        # Copy production database
        shutil.copy2(prod_db_path, test_db_path)
        print(f"Copied database from {prod_db_path} to {test_db_path}")
    else:
        # Create empty test database if production doesn't exist
        test_db_path.parent.mkdir(parents=True, exist_ok=True)
        test_db_url = f"sqlite:///{test_db_path}"
        DatabaseManager(test_db_url)  # Creates tables automatically
        print(f"Created empty test database at {test_db_path}")

    return test_db_path


@pytest.fixture(scope="function")
def test_db_manager(test_database_path, monkeypatch):
    """Provide test database manager with isolated database."""
    test_db_url = f"sqlite:///{test_database_path}"

    # Temporarily override database URL in settings
    monkeypatch.setattr(settings, "database_url", test_db_url)

    # Create a new database manager with test database
    test_manager = DatabaseManager(test_db_url)

    yield test_manager

    # Cleanup: rollback any uncommitted changes
    # Note: We don't delete the test database to allow inspection after tests


@pytest.fixture(scope="function")
def test_session(test_db_manager) -> Generator[Session, None, None]:
    """Provide test database session."""
    with test_db_manager.get_session() as session:
        yield session
        session.rollback()  # Rollback any changes after test


@pytest.fixture(scope="function")
def override_db_manager(test_db_manager, monkeypatch):
    """Override the global db_manager and FastAPI dependencies for the duration of the test."""
    from src import database

    # Save original
    original_db_manager = database.db_manager

    # Override global db_manager in database module
    monkeypatch.setattr(database, "db_manager", test_db_manager)

    # Also override db_manager in services that import it directly
    # This ensures services use the test database
    # Only patch services that actually import db_manager
    import api.services.certificate_service
    import api.services.chat_message_service
    import api.services.cover_letter_service
    import api.services.education_service
    import api.services.experience_service
    import api.services.job_service
    import api.services.resume_service
    import api.services.user_service

    monkeypatch.setattr(api.services.experience_service, "db_manager", test_db_manager)
    monkeypatch.setattr(api.services.user_service, "db_manager", test_db_manager)
    monkeypatch.setattr(api.services.job_service, "db_manager", test_db_manager)
    monkeypatch.setattr(api.services.resume_service, "db_manager", test_db_manager)
    monkeypatch.setattr(api.services.cover_letter_service, "db_manager", test_db_manager)
    monkeypatch.setattr(api.services.education_service, "db_manager", test_db_manager)
    monkeypatch.setattr(api.services.certificate_service, "db_manager", test_db_manager)
    monkeypatch.setattr(api.services.chat_message_service, "db_manager", test_db_manager)

    # Also patch workflow modules that use db_manager
    import api.routes.workflows
    import api.services.job_intake_service.workflows.gap_analysis
    import api.services.job_intake_service.workflows.stakeholder_analysis

    monkeypatch.setattr(
        api.services.job_intake_service.workflows.gap_analysis, "db_manager", test_db_manager
    )
    monkeypatch.setattr(
        api.services.job_intake_service.workflows.stakeholder_analysis, "db_manager", test_db_manager
    )
    monkeypatch.setattr(api.routes.workflows, "db_manager", test_db_manager)

    # Override FastAPI dependency
    def override_get_session() -> Generator[Session, None, None]:
        """Override get_session to use test database."""
        with test_db_manager.get_session() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    yield test_db_manager

    # Restore original
    monkeypatch.setattr(database, "db_manager", original_db_manager)
    app.dependency_overrides.clear()
