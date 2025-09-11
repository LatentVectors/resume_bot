"""Database models and connection management using SQLModel."""

from contextlib import contextmanager
from pathlib import Path

from loguru import logger
from sqlmodel import Field, Session, SQLModel, create_engine, select

from .config import settings


class User(SQLModel, table=True):
    """User model with automatic database table creation."""

    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    created_at: str | None = Field(default=None)


class DatabaseManager:
    """Manages database connections and operations using SQLModel."""

    def __init__(self, db_url: str = None):
        self.db_url = db_url or settings.database_url
        self.engine = self._create_engine()
        self._init_database()

    def _create_engine(self):
        """Create SQLModel engine."""
        # Extract database path from URL
        if self.db_url.startswith("sqlite:///"):
            db_path = self.db_url.replace("sqlite:///", "")
            # Ensure parent directory exists
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            return create_engine(f"sqlite:///{db_path}")
        else:
            return create_engine("sqlite:///:memory:")

    def _init_database(self) -> None:
        """Initialize the database and create tables."""
        SQLModel.metadata.create_all(self.engine)
        logger.info("Database initialized successfully")

    @contextmanager
    def get_session(self):
        """Get a database session context manager."""
        with Session(self.engine) as session:
            yield session

    def add_user(self, user: User) -> int:
        """Add a new user to the database."""
        with self.get_session() as session:
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"Added user: {user.first_name} {user.last_name} (ID: {user.id})")
            return user.id

    def get_user(self, user_id: int) -> User | None:
        """Get a user by ID."""
        with self.get_session() as session:
            statement = select(User).where(User.id == user_id)
            return session.exec(statement).first()

    def list_users(self) -> list[User]:
        """Get all users."""
        with self.get_session() as session:
            statement = select(User).order_by(User.created_at.desc())
            return list(session.exec(statement))

    def update_user(self, user_id: int, **updates) -> User | None:
        """Update a user by ID."""
        with self.get_session() as session:
            user = session.get(User, user_id)
            if user:
                for key, value in updates.items():
                    setattr(user, key, value)
                session.add(user)
                session.commit()
                session.refresh(user)
                logger.info(f"Updated user {user_id}")
            return user

    def delete_user(self, user_id: int) -> bool:
        """Delete a user by ID."""
        with self.get_session() as session:
            user = session.get(User, user_id)
            if user:
                session.delete(user)
                session.commit()
                logger.info(f"Deleted user {user_id}")
                return True
            return False


# Global database manager instance
db_manager = DatabaseManager()
