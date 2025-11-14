"""Minimal unit tests for job API endpoints."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.database import Job, User


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
def test_job(override_db_manager, test_user):
    """Create a test job."""
    job = Job(
        user_id=test_user.id,
        job_title="Software Engineer",
        company_name="Acme Corp",
        job_description="Great job opportunity",
        status="Saved",
    )
    job_id = override_db_manager.add_job(job)
    return override_db_manager.get_job(job_id)


def test_list_jobs(client, test_user, test_job):
    """Test listing jobs."""
    response = client.get(f"/api/v1/jobs?user_id={test_user.id}")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1
    assert any(j["id"] == test_job.id for j in jobs)


def test_list_jobs_with_status_filter(client, test_user, test_job):
    """Test listing jobs with status filter."""
    response = client.get(f"/api/v1/jobs?user_id={test_user.id}&status_filter=Saved")
    assert response.status_code == 200
    jobs = response.json()
    assert isinstance(jobs, list)
    assert len(jobs) >= 1


def test_get_job(client, test_job):
    """Test getting a specific job."""
    response = client.get(f"/api/v1/jobs/{test_job.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_job.id
    assert data["job_title"] == "Software Engineer"
    assert data["company_name"] == "Acme Corp"


def test_get_job_not_found(client):
    """Test getting a non-existent job."""
    response = client.get("/api/v1/jobs/99999")
    assert response.status_code == 404


def test_create_job(client, test_user):
    """Test creating a job."""
    response = client.post(
        f"/api/v1/jobs?user_id={test_user.id}",
        json={
            "title": "Product Manager",
            "company": "Tech Inc",
            "description": "Manage products",
            "favorite": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["job_title"] == "Product Manager"
    assert data["company_name"] == "Tech Inc"
    assert data["job_description"] == "Manage products"


def test_update_job(client, test_job):
    """Test updating a job."""
    response = client.patch(
        f"/api/v1/jobs/{test_job.id}",
        json={
            "title": "Senior Engineer",
            "favorite": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_title"] == "Senior Engineer"
    assert data["is_favorite"] is True
    assert data["company_name"] == "Acme Corp"  # Unchanged


def test_update_job_not_found(client):
    """Test updating a non-existent job."""
    response = client.patch(
        "/api/v1/jobs/99999",
        json={"title": "Updated"},
    )
    assert response.status_code == 404


def test_delete_job(client, override_db_manager, test_user):
    """Test deleting a job."""
    # Create a job to delete
    job = Job(
        user_id=test_user.id,
        job_title="Temp Job",
        company_name="Temp Corp",
        job_description="Temporary",
        status="Saved",
    )
    job_id = override_db_manager.add_job(job)

    response = client.delete(f"/api/v1/jobs/{job_id}")
    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(f"/api/v1/jobs/{job_id}")
    assert get_response.status_code == 404


def test_delete_job_not_found(client):
    """Test deleting a non-existent job."""
    response = client.delete("/api/v1/jobs/99999")
    assert response.status_code == 404


def test_toggle_favorite(client, test_job):
    """Test toggling favorite status."""
    response = client.patch(f"/api/v1/jobs/{test_job.id}/favorite?favorite=true")
    assert response.status_code == 200
    data = response.json()
    assert data["is_favorite"] is True


def test_update_status(client, test_job):
    """Test updating job status."""
    response = client.patch(f"/api/v1/jobs/{test_job.id}/status?status=Applied")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Applied"


def test_mark_as_applied(client, test_job):
    """Test marking job as applied."""
    response = client.post(f"/api/v1/jobs/{test_job.id}/apply")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Applied"
