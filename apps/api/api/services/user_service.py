"""Service for user operations."""

from datetime import datetime, timedelta

from sqlmodel import func, select

from src.database import Job, User, db_manager
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
                value = user_data.get(field, "").strip()
                if value:
                    user_data[field] = value
                else:
                    user_data[field] = ""

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

            # Normalize URL fields if provided
            url_fields = ["linkedin_url", "github_url", "website_url"]
            for field in url_fields:
                if field in updates:
                    value = updates[field].strip() if updates[field] else ""
                    updates[field] = value

            return db_manager.update_user(user_id, **updates)
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            raise

    @staticmethod
    def get_user_stats(user_id: int) -> dict:
        """Get statistics for a user's job applications.

        Returns:
            Dictionary with statistics including:
            - jobs_applied_7_days: Count of jobs applied in last 7 days
            - jobs_applied_30_days: Count of jobs applied in last 30 days
            - total_jobs_saved: Total jobs with status 'Saved'
            - total_jobs_applied: Total jobs with status 'Applied' (all time)
            - total_interviews: Total jobs with status 'Interviewing'
            - total_offers: Total jobs with status 'Hired'
            - total_favorites: Total favorite jobs
            - success_rate: Success rate (offers / applications) as percentage
        """
        if not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("Invalid user ID")

        try:
            with db_manager.get_session() as session:
                now = datetime.now()
                seven_days_ago = now - timedelta(days=7)
                thirty_days_ago = now - timedelta(days=30)

                # Jobs applied in last 7 days
                stmt_7d = (
                    select(func.count(Job.id))
                    .where(Job.user_id == user_id)
                    .where(Job.status == "Applied")
                    .where(Job.applied_at >= seven_days_ago)
                )
                jobs_applied_7_days = session.exec(stmt_7d).one() or 0

                # Jobs applied in last 30 days
                stmt_30d = (
                    select(func.count(Job.id))
                    .where(Job.user_id == user_id)
                    .where(Job.status == "Applied")
                    .where(Job.applied_at >= thirty_days_ago)
                )
                jobs_applied_30_days = session.exec(stmt_30d).one() or 0

                # Total jobs saved
                stmt_saved = (
                    select(func.count(Job.id))
                    .where(Job.user_id == user_id)
                    .where(Job.status == "Saved")
                )
                total_jobs_saved = session.exec(stmt_saved).one() or 0

                # Total jobs applied (all time)
                stmt_applied = (
                    select(func.count(Job.id))
                    .where(Job.user_id == user_id)
                    .where(Job.status == "Applied")
                )
                total_jobs_applied = session.exec(stmt_applied).one() or 0

                # Total interviews
                stmt_interviews = (
                    select(func.count(Job.id))
                    .where(Job.user_id == user_id)
                    .where(Job.status == "Interviewing")
                )
                total_interviews = session.exec(stmt_interviews).one() or 0

                # Total offers
                stmt_offers = (
                    select(func.count(Job.id))
                    .where(Job.user_id == user_id)
                    .where(Job.status == "Hired")
                )
                total_offers = session.exec(stmt_offers).one() or 0

                # Total favorites
                stmt_favorites = (
                    select(func.count(Job.id))
                    .where(Job.user_id == user_id)
                    .where(Job.is_favorite.is_(True))
                )
                total_favorites = session.exec(stmt_favorites).one() or 0

                # Success rate (offers / applications) as percentage
                success_rate = None
                if total_jobs_applied > 0:
                    success_rate = round((total_offers / total_jobs_applied) * 100, 2)

                return {
                    "jobs_applied_7_days": jobs_applied_7_days,
                    "jobs_applied_30_days": jobs_applied_30_days,
                    "total_jobs_saved": total_jobs_saved,
                    "total_jobs_applied": total_jobs_applied,
                    "total_interviews": total_interviews,
                    "total_offers": total_offers,
                    "total_favorites": total_favorites,
                    "success_rate": success_rate,
                }
        except Exception as e:
            logger.error(f"Error getting stats for user {user_id}: {e}")
            raise

