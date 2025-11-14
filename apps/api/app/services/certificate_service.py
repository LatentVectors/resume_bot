"""Service for certification operations."""

from datetime import date

from src.database import Certification, db_manager
from src.logging_config import logger


class CertificateService:
    """Service for certification CRUD operations."""

    @staticmethod
    def create_certification(user_id: int, **data) -> int:
        """Create a new certification entry with created_at/updated_at timestamps."""
        try:
            # Validate user
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")

            # Validate required fields
            required_fields = ["title", "date"]
            for field in required_fields:
                if not data.get(field):
                    raise ValueError(f"{field.replace('_', ' ').title()} is required")

            # Parse date if provided as string
            cert_date = data.get("date")
            if isinstance(cert_date, str):
                data["date"] = date.fromisoformat(cert_date)

            certification = Certification(user_id=user_id, **data)
            return db_manager.add_certification(certification)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error creating certification: {e}")
            raise

    @staticmethod
    def list_user_certifications(user_id: int) -> list[Certification]:
        """Get all certifications for a user."""
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise ValueError("Invalid user ID")
            return db_manager.list_user_certifications(user_id)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error listing certifications for user {user_id}: {e}")
            return []

    @staticmethod
    def get_certification(certification_id: int) -> Certification | None:
        """Get a certification by ID."""
        try:
            if not isinstance(certification_id, int) or certification_id <= 0:
                raise ValueError("Invalid certification ID")
            return db_manager.get_certification(certification_id)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error getting certification {certification_id}: {e}")
            return None

    @staticmethod
    def update_certification(certification_id: int, **updates) -> Certification | None:
        """Update a certification entry and set updated_at timestamp."""
        try:
            if not isinstance(certification_id, int) or certification_id <= 0:
                raise ValueError("Invalid certification ID")

            # Parse date if updated as string
            if "date" in updates and isinstance(updates["date"], str):
                updates["date"] = date.fromisoformat(updates["date"])  # type: ignore[assignment]

            return db_manager.update_certification(certification_id, **updates)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error updating certification {certification_id}: {e}")
            raise

    @staticmethod
    def delete_certification(certification_id: int) -> bool:
        """Delete a certification entry."""
        try:
            if not isinstance(certification_id, int) or certification_id <= 0:
                raise ValueError("Invalid certification ID")
            return db_manager.delete_certification(certification_id)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error deleting certification {certification_id}: {e}")
            return False
