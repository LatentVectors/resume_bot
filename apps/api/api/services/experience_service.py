"""Service for experience operations."""

from __future__ import annotations

from datetime import date

from src.database import Achievement, Experience, db_manager
from src.logging_config import logger


class ExperienceService:
    """Service for experience operations."""

    @staticmethod
    def create_experience(user_id: int, **data) -> int:
        """Create a new experience entry with created_at/updated_at timestamps.

        Accepts optional `location` and persists it if provided (empty strings coerced to None).
        """
        try:
            # Validate user exists
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")

            # Check if user exists
            user = db_manager.get_user(user_id)
            if not user:
                raise ValueError(f"User with ID {user_id} not found")

            # Validate required fields
            required_fields = ["company_name", "job_title", "start_date"]
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Normalize optional location
            if "location" in data:
                data["location"] = _normalize_optional_str(data.get("location"))

            # Validate date format and logic
            start_date = _coerce_iso_date(data["start_date"])  # type: ignore[index]
            end_date = _coerce_iso_date(data.get("end_date"))
            data["start_date"] = start_date
            if end_date is not None:
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
                start_date = _coerce_iso_date(updates.get("start_date"))
                end_date = _coerce_iso_date(updates.get("end_date"))

                if start_date is not None:
                    updates["start_date"] = start_date
                if end_date is not None:
                    updates["end_date"] = end_date

                if start_date and end_date and start_date > end_date:
                    raise ValueError("Start date must be before end date")

            # Normalize optional location if provided
            if "location" in updates:
                updates["location"] = _normalize_optional_str(updates.get("location"))

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

    @staticmethod
    def update_experience_fields(
        experience_id: int,
        company_overview: str | None = None,
        role_overview: str | None = None,
        skills: list[str] | None = None,
    ) -> Experience | None:
        """Update enhanced experience fields (company_overview, role_overview, skills).

        Args:
            experience_id: ID of the experience to update.
            company_overview: Optional overview of the company.
            role_overview: Optional overview of the role.
            skills: Optional list of skills for this role.

        Returns:
            Updated Experience object, or None if not found.
        """
        try:
            if not isinstance(experience_id, int) or experience_id <= 0:
                raise ValueError("Invalid experience ID")

            updates: dict[str, object] = {}
            if company_overview is not None:
                updates["company_overview"] = _normalize_optional_str(company_overview)
            if role_overview is not None:
                updates["role_overview"] = _normalize_optional_str(role_overview)
            if skills is not None:
                # Filter out empty strings and strip whitespace from skills
                updates["skills"] = [s.strip() for s in skills if s and s.strip()]

            if not updates:
                return db_manager.get_experience(experience_id)

            return db_manager.update_experience(experience_id, **updates)
        except Exception as e:
            logger.exception(f"Error updating experience fields for {experience_id}: {e}")
            raise

    @staticmethod
    def add_achievement(experience_id: int, title: str, content: str, order: int | None = None) -> int:
        """Add a new achievement to an experience.

        Args:
            experience_id: ID of the parent experience.
            title: Title/headline of the achievement.
            content: Content/description of the achievement.
            order: Optional order value. If not provided, appends to the end.

        Returns:
            ID of the created achievement.
        """
        try:
            if not isinstance(experience_id, int) or experience_id <= 0:
                raise ValueError("Invalid experience ID")
            if not title or not title.strip():
                raise ValueError("Achievement title is required")
            if not content or not content.strip():
                raise ValueError("Achievement content is required")

            # Verify experience exists
            experience = db_manager.get_experience(experience_id)
            if not experience:
                raise ValueError(f"Experience {experience_id} not found")

            # If no order specified, append to the end
            if order is None:
                existing = db_manager.list_experience_achievements(experience_id)
                order = len(existing)

            achievement = Achievement(
                experience_id=experience_id, title=title.strip(), content=content.strip(), order=order
            )
            achievement_id = db_manager.add_achievement(achievement)
            logger.info(f"Added achievement {achievement_id} to experience {experience_id}")
            return achievement_id
        except Exception as e:
            logger.exception(f"Error adding achievement to experience {experience_id}: {e}")
            raise

    @staticmethod
    def update_achievement(achievement_id: int, title: str, content: str) -> Achievement | None:
        """Update an achievement's title and content.

        Args:
            achievement_id: ID of the achievement to update.
            title: New title for the achievement.
            content: New content for the achievement.

        Returns:
            Updated Achievement object, or None if not found.
        """
        try:
            if not isinstance(achievement_id, int) or achievement_id <= 0:
                raise ValueError("Invalid achievement ID")
            if not title or not title.strip():
                raise ValueError("Achievement title is required")
            if not content or not content.strip():
                raise ValueError("Achievement content is required")

            return db_manager.update_achievement(achievement_id, title=title.strip(), content=content.strip())
        except Exception as e:
            logger.exception(f"Error updating achievement {achievement_id}: {e}")
            raise

    @staticmethod
    def delete_achievement(achievement_id: int) -> bool:
        """Delete an achievement.

        Args:
            achievement_id: ID of the achievement to delete.

        Returns:
            True if deleted successfully, False otherwise.
        """
        if not isinstance(achievement_id, int) or achievement_id <= 0:
            raise ValueError("Invalid achievement ID")

        try:
            return db_manager.delete_achievement(achievement_id)
        except Exception as e:
            logger.exception(f"Error deleting achievement {achievement_id}: {e}")
            return False

    @staticmethod
    def reorder_achievements(experience_id: int, achievement_ids_in_order: list[int]) -> bool:
        """Reorder achievements for an experience.

        Args:
            experience_id: ID of the parent experience.
            achievement_ids_in_order: List of achievement IDs in the desired order.

        Returns:
            True if reordering succeeded, False otherwise.
        """
        if not isinstance(experience_id, int) or experience_id <= 0:
            raise ValueError("Invalid experience ID")
        if not achievement_ids_in_order:
            raise ValueError("Achievement IDs list is required")

        try:
            # Verify all achievements belong to the experience
            existing = db_manager.list_experience_achievements(experience_id)
            existing_ids = {a.id for a in existing}
            provided_ids = set(achievement_ids_in_order)

            if existing_ids != provided_ids:
                raise ValueError("Provided achievement IDs do not match existing achievements for this experience")

            # Update order for each achievement
            for new_order, achievement_id in enumerate(achievement_ids_in_order):
                db_manager.update_achievement(achievement_id, order=new_order)

            logger.info(f"Reordered {len(achievement_ids_in_order)} achievements for experience {experience_id}")
            return True
        except ValueError:
            # Re-raise ValueError for invalid inputs
            raise
        except Exception as e:
            logger.exception(f"Error reordering achievements for experience {experience_id}: {e}")
            return False

    @staticmethod
    def get_experience_with_achievements(experience_id: int) -> tuple[Experience | None, list[Achievement]]:
        """Get an experience along with its achievements.

        Args:
            experience_id: ID of the experience to retrieve.

        Returns:
            Tuple of (Experience, list of Achievements). Experience is None if not found.
        """
        try:
            if not isinstance(experience_id, int) or experience_id <= 0:
                raise ValueError("Invalid experience ID")

            experience = db_manager.get_experience(experience_id)
            if not experience:
                return None, []

            achievements = db_manager.list_experience_achievements(experience_id)
            return experience, achievements
        except Exception as e:
            logger.exception(f"Error getting experience {experience_id} with achievements: {e}")
            return None, []


def _coerce_iso_date(value):
    """Coerce a value into a date if it's an ISO date string; pass dates/None through."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    return value


def _normalize_optional_str(value):
    """Normalize optional string fields: strip whitespace and convert empty strings to None."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped if stripped else None
    return value

