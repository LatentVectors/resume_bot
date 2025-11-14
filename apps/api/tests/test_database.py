"""Tests for database operations."""

import os
import tempfile

from src.database import DatabaseManager, User


class TestDatabaseManager:
    """Test cases for the database manager."""

    def test_database_initialization(self):
        """Test that the database can be initialized."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"

        try:
            db_manager = DatabaseManager(db_url)
            assert db_manager is not None
            assert db_manager.engine is not None
        finally:
            os.unlink(tmp.name)

    def test_user_operations(self):
        """Test user CRUD operations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"

        try:
            db_manager = DatabaseManager(db_url)

            # Create a user
            user = User(first_name="John", last_name="Doe")
            user_id = db_manager.add_user(user)

            assert user_id is not None
            assert user_id > 0

            # Retrieve the user
            retrieved_user = db_manager.get_user(user_id)
            assert retrieved_user is not None
            assert retrieved_user.first_name == "John"
            assert retrieved_user.last_name == "Doe"
            assert retrieved_user.id == user_id

            # List all users
            users = db_manager.list_users()
            assert len(users) == 1
            assert users[0].first_name == "John"

        finally:
            os.unlink(tmp.name)

    def test_user_update_and_delete(self):
        """Test user update and delete operations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_url = f"sqlite:///{tmp.name}"

        try:
            db_manager = DatabaseManager(db_url)

            # Create a user
            user = User(first_name="John", last_name="Doe")
            user_id = db_manager.add_user(user)

            # Update the user
            updated_user = db_manager.update_user(user_id, first_name="Jane", last_name="Smith")
            assert updated_user is not None
            assert updated_user.first_name == "Jane"
            assert updated_user.last_name == "Smith"

            # Verify the update
            retrieved_user = db_manager.get_user(user_id)
            assert retrieved_user.first_name == "Jane"
            assert retrieved_user.last_name == "Smith"

            # Delete the user
            deleted = db_manager.delete_user(user_id)
            assert deleted is True

            # Verify deletion
            retrieved_user = db_manager.get_user(user_id)
            assert retrieved_user is None

        finally:
            os.unlink(tmp.name)
