"""Minimal unit tests for workflow API endpoints."""

from datetime import date
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.database import Experience, User
from src.exceptions import OpenAIQuotaExceededError
from tests.conftest import override_db_manager


@pytest.fixture
def client(override_db_manager):
    """Create test client with overridden database."""
    # override_db_manager fixture already sets up dependency overrides
    return TestClient(app)


@pytest.fixture
def test_user(override_db_manager):
    """Create a test user."""
    user = User(first_name="Test", last_name="User")
    user_id = override_db_manager.add_user(user)
    return override_db_manager.get_user(user_id)


@pytest.fixture
def test_experience(override_db_manager, test_user):
    """Create a test experience."""
    experience = Experience(
        user_id=test_user.id,
        company_name="Acme Corp",
        job_title="Software Engineer",
        start_date=date(2020, 1, 1),
        end_date=date(2022, 12, 31),
    )
    exp_id = override_db_manager.add_experience(experience)
    return override_db_manager.get_experience(exp_id)


@patch("api.routes.workflows.analyze_job_experience_fit")
def test_gap_analysis(mock_analyze, client, test_experience):
    """Test gap analysis workflow."""
    # Mock the LLM call
    mock_analyze.return_value = "This is a mock gap analysis result."

    response = client.post(
        "/api/v1/workflows/gap-analysis",
        json={
            "job_description": "Looking for a software engineer with Python experience.",
            "experience_ids": [test_experience.id],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert data["analysis"] == "This is a mock gap analysis result."
    mock_analyze.assert_called_once()


@patch("api.routes.workflows.analyze_job_experience_fit")
def test_gap_analysis_quota_exceeded(mock_analyze, client, test_experience):
    """Test gap analysis with quota exceeded error."""
    # Mock the LLM call to raise quota exceeded error
    mock_analyze.side_effect = OpenAIQuotaExceededError()

    response = client.post(
        "/api/v1/workflows/gap-analysis",
        json={
            "job_description": "Looking for a software engineer.",
            "experience_ids": [test_experience.id],
        },
    )
    assert response.status_code == 429  # Too Many Requests


@patch("api.routes.workflows.analyze_stakeholders")
def test_stakeholder_analysis(mock_analyze, client, test_experience):
    """Test stakeholder analysis workflow."""
    # Mock the LLM call
    mock_analyze.return_value = "This is a mock stakeholder analysis result."

    response = client.post(
        "/api/v1/workflows/stakeholder-analysis",
        json={
            "job_description": "Looking for a software engineer.",
            "experience_ids": [test_experience.id],
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "analysis" in data
    assert data["analysis"] == "This is a mock stakeholder analysis result."
    mock_analyze.assert_called_once()


def test_gap_analysis_no_experiences(client):
    """Test gap analysis with no valid experiences."""
    response = client.post(
        "/api/v1/workflows/gap-analysis",
        json={
            "job_description": "Looking for a software engineer.",
            "experience_ids": [99999],  # Non-existent experience
        },
    )
    assert response.status_code == 400  # Bad Request
