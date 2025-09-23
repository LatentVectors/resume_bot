"""Database models and connection management using SQLModel."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from enum import Enum, StrEnum
from pathlib import Path

from sqlalchemy import Index, UniqueConstraint, text
from sqlmodel import Field, Session, SQLModel, create_engine, select

from src.logging_config import logger

from .config import settings


# Enums for constrained fields
class JobStatus(str, Enum):
    Saved = "Saved"
    Applied = "Applied"
    Interviewing = "Interviewing"
    NotSelected = "Not Selected"
    NoOffer = "No Offer"
    Hired = "Hired"


class MessageChannel(str, Enum):
    email = "email"
    linkedin = "linkedin"


class ResponseSource(str, Enum):
    manual = "manual"
    application = "application"


# specs/008-resume_history
class ResumeVersionEvent(StrEnum):
    """Event types that create a resume version.

    Values are aligned with specs/008-resume_history.
    """

    generate = "generate"
    save = "save"
    reset = "reset"


class User(SQLModel, table=True):
    """User model with automatic database table creation."""

    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    phone_number: str | None = Field(default=None)
    email: str | None = Field(default=None)
    address: str | None = Field(default=None)
    city: str | None = Field(default=None)
    state: str | None = Field(default=None)
    zip_code: str | None = Field(default=None)
    linkedin_url: str | None = Field(default=None)
    github_url: str | None = Field(default=None)
    website_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Experience(SQLModel, table=True):
    """Experience model for work experience entries."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    company_name: str
    job_title: str
    location: str | None = Field(default=None)
    start_date: date  # ISO date format (YYYY-MM-DD)
    end_date: date | None = Field(default=None)  # ISO date format (YYYY-MM-DD)
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Education(SQLModel, table=True):
    """Education model for education entries."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    institution: str
    degree: str
    major: str
    grad_date: date  # ISO date format (YYYY-MM-DD)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Certification(SQLModel, table=True):
    """Certification model for professional certifications."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str
    institution: str | None = Field(default=None)
    date: date
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Job(SQLModel, table=True):
    """Job application model for tracking resumes generated for specific jobs."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    job_description: str
    company_name: str | None = Field(default=None)
    job_title: str | None = Field(default=None)
    status: JobStatus = Field(default="Saved")
    is_favorite: bool = Field(default=False)
    applied_at: datetime | None = Field(default=None)
    has_resume: bool = Field(default=False)
    has_cover_letter: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Resume(SQLModel, table=True):
    """Resume entity storing JSON content and rendered PDF for a single job.

    Enforces a single resume per job via a uniqueness constraint on job_id.
    """

    __table_args__ = (UniqueConstraint("job_id", name="uq_resume_job_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    template_name: str
    resume_json: str
    # Deprecated as of specs/008-resume_history; unused by runtime logic. Kept for backward compatibility.
    pdf_filename: str | None = Field(default=None)
    locked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ResumeVersion(SQLModel, table=True):
    """Immutable history of resume versions per job.

    - Monotonic `version_index` starting at 1 per `job_id`
    - Uniqueness on `(job_id, version_index)`
    - Secondary index on `(job_id, created_at desc)`
    """

    __table_args__ = (
        UniqueConstraint("job_id", "version_index", name="uq_resume_version_job_id_version_index"),
        Index(
            "ix_resume_version_job_id_created_at_desc",
            "job_id",
            text("created_at DESC"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    version_index: int
    parent_version_id: int | None = Field(default=None, foreign_key=None)
    event_type: ResumeVersionEvent
    template_name: str
    resume_json: str
    created_by_user_id: int
    created_at: datetime = Field(default_factory=datetime.now)


class CoverLetter(SQLModel, table=True):
    """Placeholder Cover Letter entity storing simple text content."""

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    content: str
    locked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Message(SQLModel, table=True):
    """Minimal Message entity. Locked derives from whether the message was sent."""

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    channel: MessageChannel
    body: str
    sent_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @property
    def locked(self) -> bool:
        """Message becomes locked once it has been sent."""
        return self.sent_at is not None


class Response(SQLModel, table=True):
    """Minimal Response entity for storing generated or manual responses."""

    id: int | None = Field(default=None, primary_key=True)
    job_id: int | None = Field(default=None, foreign_key="job.id")
    prompt: str
    response: str
    source: ResponseSource
    ignore: bool = Field(default=False)
    locked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Note(SQLModel, table=True):
    """Simple note attached to a Job."""

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


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
            logger.info(
                "Initializing database engine",
                extra={"database_url": self.db_url, "db_path": str(Path(db_path).resolve())},
            )
            return create_engine(f"sqlite:///{db_path}")
        # Do not silently fall back to in-memory; this hides persistence issues
        raise ValueError("Unsupported database_url. Only sqlite:/// paths are supported. Set database_url in .env.")

    def _init_database(self) -> None:
        """Initialize the database and create tables."""
        SQLModel.metadata.create_all(self.engine)
        logger.info("Database initialized successfully")

    def reset_database(self) -> None:
        """Drop and recreate all tables.

        Intended for local development when making non-migrated schema changes.
        """
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)
        logger.info("Database schema reset successfully")

    @contextmanager
    def get_session(self):
        """Get a database session context manager."""
        with Session(self.engine) as session:
            yield session

    def add_user(self, user: User) -> int:
        """Add a new user to the database."""
        with self.get_session() as session:
            _set_timestamps_on_create(user)

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
                _touch_updated_at(user)
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

    # Experience methods
    def add_experience(self, experience: Experience) -> int:
        """Add a new experience to the database."""
        with self.get_session() as session:
            _set_timestamps_on_create(experience)

            session.add(experience)
            session.commit()
            session.refresh(experience)
            logger.info(f"Added experience: {experience.job_title} at {experience.company_name} (ID: {experience.id})")
            return experience.id

    def get_experience(self, experience_id: int) -> Experience | None:
        """Get an experience by ID."""
        with self.get_session() as session:
            return session.get(Experience, experience_id)

    def list_user_experiences(self, user_id: int) -> list[Experience]:
        """Get all experiences for a user."""
        with self.get_session() as session:
            statement = select(Experience).where(Experience.user_id == user_id).order_by(Experience.start_date.desc())
            return list(session.exec(statement))

    def update_experience(self, experience_id: int, **updates) -> Experience | None:
        """Update an experience by ID."""
        with self.get_session() as session:
            experience = session.get(Experience, experience_id)
            if experience:
                for key, value in updates.items():
                    setattr(experience, key, value)
                _touch_updated_at(experience)
                session.add(experience)
                session.commit()
                session.refresh(experience)
                logger.info(f"Updated experience {experience_id}")
            return experience

    def delete_experience(self, experience_id: int) -> bool:
        """Delete an experience by ID."""
        with self.get_session() as session:
            experience = session.get(Experience, experience_id)
            if experience:
                session.delete(experience)
                session.commit()
                logger.info(f"Deleted experience {experience_id}")
                return True
            return False

    # Certification methods
    def add_certification(self, certification: Certification) -> int:
        """Add a new certification to the database."""
        with self.get_session() as session:
            _set_timestamps_on_create(certification)

            session.add(certification)
            session.commit()
            session.refresh(certification)
            logger.info(
                f"Added certification: {certification.title} (ID: {certification.id}) for user {certification.user_id}"
            )
            return certification.id

    def get_certification(self, certification_id: int) -> Certification | None:
        """Get a certification by ID."""
        with self.get_session() as session:
            return session.get(Certification, certification_id)

    def list_user_certifications(self, user_id: int) -> list[Certification]:
        """Get all certifications for a user."""
        with self.get_session() as session:
            statement = (
                select(Certification).where(Certification.user_id == user_id).order_by(Certification.date.desc())
            )
            return list(session.exec(statement))

    def update_certification(self, certification_id: int, **updates) -> Certification | None:
        """Update a certification by ID."""
        with self.get_session() as session:
            certification = session.get(Certification, certification_id)
            if certification:
                for key, value in updates.items():
                    setattr(certification, key, value)
                _touch_updated_at(certification)
                session.add(certification)
                session.commit()
                session.refresh(certification)
                logger.info(f"Updated certification {certification_id}")
            return certification

    def delete_certification(self, certification_id: int) -> bool:
        """Delete a certification by ID."""
        with self.get_session() as session:
            certification = session.get(Certification, certification_id)
            if certification:
                session.delete(certification)
                session.commit()
                logger.info(f"Deleted certification {certification_id}")
                return True
            return False

    # Education methods
    def add_education(self, education: Education) -> int:
        """Add a new education to the database."""
        with self.get_session() as session:
            _set_timestamps_on_create(education)

            session.add(education)
            session.commit()
            session.refresh(education)
            logger.info(f"Added education: {education.degree} at {education.institution} (ID: {education.id})")
            return education.id

    def get_education(self, education_id: int) -> Education | None:
        """Get an education by ID."""
        with self.get_session() as session:
            return session.get(Education, education_id)

    def list_user_educations(self, user_id: int) -> list[Education]:
        """Get all educations for a user."""
        with self.get_session() as session:
            statement = select(Education).where(Education.user_id == user_id).order_by(Education.grad_date.desc())
            return list(session.exec(statement))

    def update_education(self, education_id: int, **updates) -> Education | None:
        """Update an education by ID."""
        with self.get_session() as session:
            education = session.get(Education, education_id)
            if education:
                for key, value in updates.items():
                    setattr(education, key, value)
                _touch_updated_at(education)
                session.add(education)
                session.commit()
                session.refresh(education)
                logger.info(f"Updated education {education_id}")
            return education

    def delete_education(self, education_id: int) -> bool:
        """Delete an education by ID."""
        with self.get_session() as session:
            education = session.get(Education, education_id)
            if education:
                session.delete(education)
                session.commit()
                logger.info(f"Deleted education {education_id}")
                return True
            return False

    # Job methods
    def add_job(self, job: Job) -> int:
        """Add a new job to the database."""
        with self.get_session() as session:
            _set_timestamps_on_create(job)

            session.add(job)
            session.commit()
            session.refresh(job)
            logger.info(f"Added job (ID: {job.id}) for user {job.user_id}")
            return job.id

    def get_job(self, job_id: int) -> Job | None:
        """Get a job by ID."""
        with self.get_session() as session:
            return session.get(Job, job_id)

    def list_jobs_by_user_id(self, user_id: int) -> list[Job]:
        """List all jobs for a given user, newest first."""
        with self.get_session() as session:
            statement = select(Job).where(Job.user_id == user_id).order_by(Job.created_at.desc())
            return list(session.exec(statement))

    def update_job(self, job_id: int, **updates) -> Job | None:
        """Update a job by ID."""
        with self.get_session() as session:
            job = session.get(Job, job_id)
            if job:
                for key, value in updates.items():
                    setattr(job, key, value)
                _touch_updated_at(job)
                session.add(job)
                session.commit()
                session.refresh(job)
                logger.info(f"Updated job {job_id}")
            return job

    def delete_job(self, job_id: int) -> bool:
        """Delete a job by ID."""
        with self.get_session() as session:
            job = session.get(Job, job_id)
            if job:
                session.delete(job)
                session.commit()
                logger.info(f"Deleted job {job_id}")
                return True
            return False

    # Response methods
    def list_responses(self, sources: list[str] | None = None, ignore: bool | None = None) -> list[Response]:
        """List responses with optional filters for source and ignore flag.

        Args:
            sources: Optional list of sources to include (e.g., ["manual", "application"]). If None or empty, includes all.
            ignore: Optional flag to filter ignored status. If None, includes both ignored and not ignored.

        Returns:
            A list of Response rows ordered by created_at desc.
        """
        with self.get_session() as session:
            statement = select(Response)
            if sources:
                statement = statement.where(Response.source.in_(tuple(sources)))
            if ignore is not None:
                statement = statement.where(Response.ignore == ignore)
            statement = statement.order_by(Response.created_at.desc())
            return list(session.exec(statement))


# Global database manager instance
db_manager = DatabaseManager()


# Timestamp helpers
def _set_timestamps_on_create(obj: SQLModel) -> None:
    """Ensure created_at/updated_at are set on object creation."""
    if getattr(obj, "created_at", None) is None:
        obj.created_at = datetime.now()  # type: ignore[attr-defined]
    if getattr(obj, "updated_at", None) is None:
        obj.updated_at = datetime.now()  # type: ignore[attr-defined]


def _touch_updated_at(obj: SQLModel) -> None:
    """Update the updated_at timestamp to now."""
    obj.updated_at = datetime.now()  # type: ignore[attr-defined]
