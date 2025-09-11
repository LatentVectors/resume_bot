"""Service for education operations."""

from datetime import date

from loguru import logger

from src.database import Education, User, db_manager


class EducationService:
    """Service for education operations."""

    @staticmethod
    def create_education(user_id: int, **data) -> int:
        """Create a new education entry with created_at/updated_at timestamps."""
        try:
            # Validate user exists
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")

            # Check if user exists
            user = db_manager.get_user(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Validate required fields
            required_fields = ["school", "degree", "start_date", "end_date"]
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Validate date format and logic
            start_date = data["start_date"]
            end_date = data["end_date"]

            if isinstance(start_date, str):
                start_date = date.fromisoformat(start_date)
                data["start_date"] = start_date

            if isinstance(end_date, str):
                end_date = date.fromisoformat(end_date)
                data["end_date"] = end_date

            if start_date and end_date and start_date > end_date:
                raise ValueError("Start date must be before end date")

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
