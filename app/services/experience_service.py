"""Service for experience operations."""

from datetime import date

from src.database import Experience, User, db_manager
from src.logging_config import logger


class ExperienceService:
    """Service for experience operations."""

    @staticmethod
    def create_experience(user_id: int, **data) -> int:
        """Create a new experience entry with created_at/updated_at timestamps."""
        try:
            # Validate user exists
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")

            # Check if user exists
            user = db_manager.get_user(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Validate required fields
            required_fields = ["company_name", "job_title", "start_date", "content"]
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Validate date format and logic
            start_date = data["start_date"]
            end_date = data.get("end_date")

            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
                data["start_date"] = start_date

            if end_date:
                if isinstance(end_date, str):
                    end_date = date.fromisoformat(end_date)
                    data["end_date"] = end_date

                if start_date and end_date and start_date > end_date:
                    raise ValueError("Start date must be before end date")

            experience = Experience(user_id=user_id, **data)
            return db_manager.add_experience(experience)
        except Exception as e:
            logger.error(f"Error creating experience: {e}")
            raise

    @staticmethod
    def list_user_experiences(user_id: int) -> list[Experience]:
        """Get all experiences for a user."""
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")
            return db_manager.list_user_experiences(user_id)
        except Exception as e:
            logger.error(f"Error listing experiences for user {user_id}: {e}")
            return []

    @staticmethod
    def get_experience(experience_id: int) -> Experience | None:
        """Get an experience by ID."""
        try:
            if not isinstance(experience_id, int) or experience_id <= 0:
                raise ValueError("Invalid experience ID")
            return db_manager.get_experience(experience_id)
        except Exception as e:
            logger.error(f"Error getting experience {experience_id}: {e}")
            return None

    @staticmethod
    def update_experience(experience_id: int, **updates) -> Experience | None:
        """Update an experience entry and set updated_at timestamp."""
        try:
            if not isinstance(experience_id, int) or experience_id <= 0:
                raise ValueError("Invalid experience ID")

            # Validate date logic if dates are being updated
            if "start_date" in updates or "end_date" in updates:
                start_date = updates.get("start_date")
                end_date = updates.get("end_date")

                if start_date and isinstance(start_date, str):
                    start_date = date.fromisoformat(start_date)
                    updates["start_date"] = start_date

                if end_date and isinstance(end_date, str):
                    end_date = date.fromisoformat(end_date)
                    updates["end_date"] = end_date

                if start_date and end_date and start_date > end_date:
                    raise ValueError("Start date must be before end date")

            return db_manager.update_experience(experience_id, **updates)
        except Exception as e:
            logger.error(f"Error updating experience {experience_id}: {e}")
            raise

    @staticmethod
    def delete_experience(experience_id: int) -> bool:
        """Delete an experience entry."""
        try:
            if not isinstance(experience_id, int) or experience_id <= 0:
                raise ValueError("Invalid experience ID")
            return db_manager.delete_experience(experience_id)
        except Exception as e:
            logger.error(f"Error deleting experience {experience_id}: {e}")
            return False
