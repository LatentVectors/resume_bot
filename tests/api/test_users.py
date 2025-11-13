"""Minimal unit tests for user API endpoints."""

import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.database import User
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


def test_list_users(client, test_user):
    """Test listing users."""
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert len(users) >= 1
    assert any(u["id"] == test_user.id for u in users)


def test_get_user(client, test_user):
    """Test getting a specific user."""
    response = client.get(f"/api/v1/users/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id
    assert data["first_name"] == "Test"
    assert data["last_name"] == "User"


def test_get_user_not_found(client):
    """Test getting a non-existent user."""
    response = client.get("/api/v1/users/99999")
    assert response.status_code == 404


def test_create_user(client, override_db_manager):
    """Test creating a user."""
    response = client.post(
        "/api/v1/users",
        json={
            "first_name": "New",
            "last_name": "User",
            "email": "new@example.com",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["first_name"] == "New"
    assert data["last_name"] == "User"
    assert data["email"] == "new@example.com"


def test_update_user(client, test_user):
    """Test updating a user."""
    response = client.patch(
        f"/api/v1/users/{test_user.id}",
        json={
            "first_name": "Updated",
            "email": "updated@example.com",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Updated"
    assert data["email"] == "updated@example.com"
    assert data["last_name"] == "User"  # Unchanged


def test_update_user_not_found(client):
    """Test updating a non-existent user."""
    response = client.patch(
        "/api/v1/users/99999",
        json={"first_name": "Updated"},
    )
    assert response.status_code == 404


def test_get_current_user(client, test_user):
    """Test getting current user."""
    response = client.get("/api/v1/users/current")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_user.id

