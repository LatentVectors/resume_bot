from src.database import User, db_manager


class UserService:
    """Service for user operations."""

    @staticmethod
    def create_user(first_name: str, last_name: str) -> int:
        """Create a new user."""
        return db_manager.add_user(User(first_name=first_name, last_name=last_name))

    @staticmethod
    def get_user(user_id: int) -> User | None:
        """Get a user by ID."""
        return db_manager.get_user(user_id)

    @staticmethod
    def list_users() -> list[User]:
        """Get all users."""
        return db_manager.list_users()
