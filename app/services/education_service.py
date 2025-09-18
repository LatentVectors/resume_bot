"""Service for education operations."""

from datetime import date

from src.database import Education, User, db_manager
from src.logging_config import logger


class EducationService:
    """Service for education operations."""

    @staticmethod
    def create_education(user_id: int, **data) -> int:
        """Create a new education entry with created_at/updated_at timestamps.

        Expects fields aligned with the Education schema:
        - institution: str
        - degree: str
        - major: str
        - grad_date: date | ISO date str (YYYY-MM-DD)
        """
        try:
            # Validate user exists
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")

            # Check if user exists
            user = db_manager.get_user(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Validate required fields (new schema)
            required_fields = ["institution", "degree", "major", "grad_date"]
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Parse grad_date if provided as string
            grad_date = data["grad_date"]
            if isinstance(grad_date, str):
                grad_date = date.fromisoformat(grad_date)
                data["grad_date"] = grad_date

            education = Education(user_id=user_id, **data)
            return db_manager.add_education(education)
        except Exception as e:
            logger.error(f"Error creating education: {e}")
            raise

    @staticmethod
    def list_user_educations(user_id: int) -> list[Education]:
        """Get all educations for a user."""
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")
            return db_manager.list_user_educations(user_id)
        except Exception as e:
            logger.error(f"Error listing educations for user {user_id}: {e}")
            return []

    @staticmethod
    def get_education(education_id: int) -> Education | None:
        """Get an education by ID."""
        try:
            if not isinstance(education_id, int) or education_id <= 0:
                raise ValueError("Invalid education ID")
            return db_manager.get_education(education_id)
        except Exception as e:
            logger.error(f"Error getting education {education_id}: {e}")
            return None

    @staticmethod
    def update_education(education_id: int, **updates) -> Education | None:
        """Update an education entry and set updated_at timestamp."""
        try:
            if not isinstance(education_id, int) or education_id <= 0:
                raise ValueError("Invalid education ID")

            # Parse grad_date if provided as string
            if "grad_date" in updates:
                grad_date = updates.get("grad_date")
                if grad_date and isinstance(grad_date, str):
                    updates["grad_date"] = date.fromisoformat(grad_date)

            return db_manager.update_education(education_id, **updates)
        except Exception as e:
            logger.error(f"Error updating education {education_id}: {e}")
            raise

    @staticmethod
    def delete_education(education_id: int) -> bool:
        """Delete an education entry."""
        try:
            if not isinstance(education_id, int) or education_id <= 0:
                raise ValueError("Invalid education ID")
            return db_manager.delete_education(education_id)
        except Exception as e:
            logger.error(f"Error deleting education {education_id}: {e}")
            return False
