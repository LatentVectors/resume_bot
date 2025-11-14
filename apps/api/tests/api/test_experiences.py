"""Minimal unit tests for experience API endpoints."""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.database import Experience, User


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


def test_list_experiences(client, test_user, test_experience):
    """Test listing experiences."""
    response = client.get(f"/api/v1/experiences?user_id={test_user.id}")
    assert response.status_code == 200
    experiences = response.json()
    assert isinstance(experiences, list)
    assert len(experiences) >= 1
    assert any(e["id"] == test_experience.id for e in experiences)


def test_get_experience(client, test_experience):
    """Test getting a specific experience."""
    response = client.get(f"/api/v1/experiences/{test_experience.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_experience.id
    assert data["company_name"] == "Acme Corp"
    assert data["job_title"] == "Software Engineer"


def test_get_experience_not_found(client):
    """Test getting a non-existent experience."""
    response = client.get("/api/v1/experiences/99999")
    assert response.status_code == 404


def test_create_experience(client, test_user):
    """Test creating an experience."""
    response = client.post(
        f"/api/v1/experiences?user_id={test_user.id}",
        json={
            "company_name": "Tech Inc",
            "job_title": "Developer",
            "start_date": "2021-01-01",
            "end_date": "2023-12-31",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["company_name"] == "Tech Inc"
    assert data["job_title"] == "Developer"


def test_update_experience(client, test_experience):
    """Test updating an experience."""
    response = client.patch(
        f"/api/v1/experiences/{test_experience.id}",
        json={
            "job_title": "Senior Engineer",
            "location": "San Francisco",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_title"] == "Senior Engineer"
    assert data["location"] == "San Francisco"
    assert data["company_name"] == "Acme Corp"  # Unchanged


def test_update_experience_not_found(client):
    """Test updating a non-existent experience."""
    response = client.patch(
        "/api/v1/experiences/99999",
        json={"job_title": "Updated"},
    )
    assert response.status_code == 404


def test_delete_experience(client, override_db_manager, test_user):
    """Test deleting an experience."""
    # Create an experience to delete
    experience = Experience(
        user_id=test_user.id,
        company_name="Temp Corp",
        job_title="Temp Role",
        start_date=date(2020, 1, 1),
    )
    exp_id = override_db_manager.add_experience(experience)

    response = client.delete(f"/api/v1/experiences/{exp_id}")
    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(f"/api/v1/experiences/{exp_id}")
    assert get_response.status_code == 404


def test_delete_experience_not_found(client):
    """Test deleting a non-existent experience."""
    response = client.delete("/api/v1/experiences/99999")
    assert response.status_code == 404


def test_list_achievements(client, test_experience):
    """Test listing achievements for an experience."""
    response = client.get(f"/api/v1/experiences/{test_experience.id}/achievements")
    assert response.status_code == 200
    achievements = response.json()
    assert isinstance(achievements, list)

