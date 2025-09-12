from src.database import User, db_manager
from src.logging_config import logger


class UserService:
    """Service for user operations."""

    @staticmethod
    def has_users() -> bool:
        """Check if any users exist in the database."""
        try:
            users = db_manager.list_users()
            return len(users) > 0
        except Exception as e:
            logger.error(f"Error checking if users exist: {e}")
            return False

    @staticmethod
    def get_current_user() -> User | None:
        """Get the single user (for single-user app)."""
        try:
            users = db_manager.list_users()
            return users[0] if users else None
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None

    @staticmethod
    def create_user(**user_data) -> int:
        """Create a new user with all metadata fields."""
        try:
            # Validate required fields
            if not user_data.get("first_name") or not user_data.get("last_name"):
                raise ValueError("First name and last name are required")

            # Validate email format if provided
            if user_data.get("email") and "@" not in user_data["email"]:
                raise ValueError("Invalid email format")

            # Validate URL formats if provided
            url_fields = ["linkedin_url", "github_url", "website_url"]
            for field in url_fields:
                if user_data.get(field) and not user_data[field].startswith(("http://", "https://")):
                    user_data[field] = f"https://{user_data[field]}"

            user = User(**user_data)
            return db_manager.add_user(user)
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise

    @staticmethod
    def get_user(user_id: int) -> User | None:
        """Get a user by ID."""
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")
            return db_manager.get_user(user_id)
        except Exception as e:
            logger.error(f"Error getting user {user_id}: {e}")
            return None

    @staticmethod
    def list_users() -> list[User]:
        """Get all users."""
        try:
            return db_manager.list_users()
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return []

    @staticmethod
    def update_user(user_id: int, **updates) -> User | None:
        """Update user information and set updated_at timestamp."""
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")

            # Validate email format if provided
            if updates.get("email") and "@" not in updates["email"]:
                raise ValueError("Invalid email format")

            # Validate URL formats if provided
            url_fields = ["linkedin_url", "github_url", "website_url"]
            for field in url_fields:
                if updates.get(field) and not updates[field].startswith(("http://", "https://")):
                    updates[field] = f"https://{updates[field]}"

            return db_manager.update_user(user_id, **updates)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise
