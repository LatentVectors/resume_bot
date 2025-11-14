"""Database models and connection management using SQLModel."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from enum import Enum, StrEnum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel
from pydantic import Field as PydanticField
from sqlalchemy import Column, Index, UniqueConstraint, inspect, text
from sqlalchemy.types import JSON
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


class ProposalType(str, Enum):
    achievement_add = "achievement_add"
    achievement_update = "achievement_update"
    achievement_delete = "achievement_delete"
    skill_add = "skill_add"
    skill_delete = "skill_delete"
    role_overview_update = "role_overview_update"
    company_overview_update = "company_overview_update"


class ProposalStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"


# ==================== Pydantic Models for Proposal Content ===================


class RoleOverviewUpdate(BaseModel):
    """Update suggestion for a role overview."""

    command: Literal["UPDATE"] = PydanticField(default="UPDATE", description="The operation to perform")
    experience_id: int = PydanticField(description="The unique identifier of the work experience entry to update")
    content: str = PydanticField(description="The complete, new text for the role overview")


class CompanyOverviewUpdate(BaseModel):
    """Update suggestion for a company overview."""

    command: Literal["UPDATE"] = PydanticField(default="UPDATE", description="The operation to perform")
    experience_id: int = PydanticField(description="The unique identifier of the work experience entry to update")
    content: str = PydanticField(description="The complete, new text for the company overview")


class SkillAdd(BaseModel):
    """Add suggestion for new skills."""

    command: Literal["ADD"] = PydanticField(default="ADD", description="The operation to perform")
    experience_id: int = PydanticField(
        description="The unique identifier of the work experience entry to add skills to"
    )
    skills: list[str] = PydanticField(description="A list of new, granular skills to add")


class SkillDelete(BaseModel):
    """Delete suggestion for skills."""

    command: Literal["DELETE"] = PydanticField(default="DELETE", description="The operation to perform")
    experience_id: int = PydanticField(
        description="The unique identifier of the work experience entry to delete skills from"
    )
    skills: list[str] = PydanticField(description="A list of skills to delete")


class AchievementAdd(BaseModel):
    """Add suggestion for a new achievement."""

    command: Literal["ADD"] = PydanticField(default="ADD", description="The operation to perform")
    experience_id: int = PydanticField(description="The unique identifier of the parent work experience")
    title: str = PydanticField(description="The required title for the new achievement")
    content: str = PydanticField(description="The full content of the new achievement")


class AchievementUpdate(BaseModel):
    """Update suggestion for an existing achievement."""

    command: Literal["UPDATE"] = PydanticField(default="UPDATE", description="The operation to perform")
    experience_id: int = PydanticField(description="The unique identifier of the parent work experience")
    achievement_id: int = PydanticField(description="The required unique identifier of the achievement to update")
    title: str | None = PydanticField(
        default=None, description="An optional new title. If null or omitted, the existing title is preserved"
    )
    content: str = PydanticField(description="The complete, new text for the achievement's content")


class AchievementDelete(BaseModel):
    """Delete suggestion for an achievement."""

    command: Literal["DELETE"] = PydanticField(default="DELETE", description="The operation to perform")
    experience_id: int = PydanticField(description="The unique identifier of the parent work experience")
    achievement_id: int = PydanticField(description="The required unique identifier of the achievement to delete")


# Union type for all proposal content types
ProposalContent = (
    RoleOverviewUpdate
    | CompanyOverviewUpdate
    | SkillAdd
    | SkillDelete
    | AchievementAdd
    | AchievementUpdate
    | AchievementDelete
)


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
    """Experience model for work experience entries.

    Experience details are stored with optional fields (company_overview, role_overview, skills).
    Detailed content is tracked through associated Achievement records in a one-to-many relationship.
    """

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    company_name: str
    job_title: str
    location: str | None = Field(default=None)
    start_date: date  # ISO date format (YYYY-MM-DD)
    end_date: date | None = Field(default=None)  # ISO date format (YYYY-MM-DD)
    company_overview: str | None = Field(default=None)
    role_overview: str | None = Field(default=None)
    skills: list[str] = Field(default_factory=list, sa_column=Column(JSON))
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


class Achievement(SQLModel, table=True):
    """Achievement entries linked to specific work experiences.

    One-to-many relationship: each experience can have multiple achievements.
    Achievements are ordered via the order field for user-controlled sequencing.
    """

    id: int | None = Field(default=None, primary_key=True)
    experience_id: int = Field(foreign_key="experience.id")
    title: str  # Achievement title/headline
    content: str  # Detailed achievement description
    order: int = Field(default=0)  # For ordering achievements within experience
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
    """Cover Letter entity storing JSON content and template reference.

    Enforces a single cover letter per job via a uniqueness constraint on job_id.
    """

    __table_args__ = (UniqueConstraint("job_id", name="uq_cover_letter_job_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    cover_letter_json: str
    template_name: str = Field(default="cover_000.html")
    locked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class CoverLetterVersion(SQLModel, table=True):
    """Immutable history of cover letter versions per job.

    - Monotonic `version_index` starting at 1 per `job_id`
    - Uniqueness on `(job_id, version_index)`
    - Secondary index on `(job_id, created_at desc)`
    """

    __table_args__ = (
        UniqueConstraint("job_id", "version_index", name="uq_cover_letter_version_job_id_version_index"),
        Index(
            "ix_cover_letter_version_job_id_created_at_desc",
            "job_id",
            text("created_at DESC"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    cover_letter_id: int = Field(foreign_key="coverletter.id")
    job_id: int = Field(foreign_key="job.id")
    version_index: int
    cover_letter_json: str
    template_name: str
    created_by_user_id: int
    created_at: datetime = Field(default_factory=datetime.now)


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


class JobIntakeSession(SQLModel, table=True):
    """Tracks state of job intake workflow for resumption and analytics.

    Analysis fields store markdown-formatted content (not JSON).
    Unique constraint on job_id ensures one active session per job.
    """

    __table_args__ = (UniqueConstraint("job_id", name="uq_job_intake_session_job_id"),)

    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id")
    current_step: int  # 1, 2, or 3
    step1_completed: bool = Field(default=False)
    step2_completed: bool = Field(default=False)
    step3_completed: bool = Field(default=False)
    gap_analysis: str | None = Field(default=None)  # Renamed from gap_analysis_json (stores markdown)
    stakeholder_analysis: str | None = Field(default=None)  # NEW (stores markdown)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class JobIntakeChatMessage(SQLModel, table=True):
    """Stores chat history for intake flow steps 2 and 3.

    Messages stored as JSON to accommodate any LangChain message format.
    """

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="jobintakesession.id")
    step: int  # 2 or 3
    messages: str  # JSON array of LangChain message format
    created_at: datetime = Field(default_factory=datetime.now)


class ExperienceProposal(SQLModel, table=True):
    """Proposals for updating experience entries based on Step 2 conversation analysis.

    Stores AI-generated suggestions for updating experiences, achievements, and skills.
    Proposals can be edited, accepted, or rejected by the user.
    """

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="jobintakesession.id")
    proposal_type: ProposalType
    experience_id: int = Field(foreign_key="experience.id")
    achievement_id: int | None = Field(
        default=None, foreign_key="achievement.id"
    )  # Only for achievement updates/deletes
    proposed_content: str  # JSON containing the full proposal data (Pydantic model serialized to JSON)
    original_proposed_content: str  # JSON of the original AI-generated proposal (for revert functionality)
    status: ProposalStatus  # enum: 'pending', 'accepted', 'rejected'
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    def parse_proposed_content(self) -> ProposalContent:
        """Parse and validate proposed_content JSON string, return typed Pydantic model.

        Returns:
            Typed Pydantic model instance matching the proposal content structure.

        Raises:
            ValueError: If JSON is invalid or cannot be parsed into a valid ProposalContent model.
        """
        import json

        try:
            data = json.loads(self.proposed_content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in proposed_content: {exc}") from exc

        # Use Pydantic's model_validate to parse based on command field
        command = data.get("command")
        if command == "UPDATE":
            if "achievement_id" in data:
                return AchievementUpdate.model_validate(data)
            elif self.proposal_type == ProposalType.role_overview_update:
                return RoleOverviewUpdate.model_validate(data)
            elif self.proposal_type == ProposalType.company_overview_update:
                return CompanyOverviewUpdate.model_validate(data)
        elif command == "ADD":
            if "title" in data:
                return AchievementAdd.model_validate(data)
            elif "skills" in data:
                return SkillAdd.model_validate(data)
        elif command == "DELETE":
            if "achievement_id" in data:
                return AchievementDelete.model_validate(data)
            elif "skills" in data:
                return SkillDelete.model_validate(data)

        # Fallback: try to validate against proposal_type
        if self.proposal_type == ProposalType.role_overview_update:
            return RoleOverviewUpdate.model_validate(data)
        elif self.proposal_type == ProposalType.company_overview_update:
            return CompanyOverviewUpdate.model_validate(data)
        elif self.proposal_type == ProposalType.skill_add:
            return SkillAdd.model_validate(data)
        elif self.proposal_type == ProposalType.skill_delete:
            return SkillDelete.model_validate(data)
        elif self.proposal_type == ProposalType.achievement_add:
            return AchievementAdd.model_validate(data)
        elif self.proposal_type == ProposalType.achievement_update:
            return AchievementUpdate.model_validate(data)
        elif self.proposal_type == ProposalType.achievement_delete:
            return AchievementDelete.model_validate(data)

        raise ValueError(f"Unable to parse proposed_content for proposal_type {self.proposal_type}")

    def parse_original_proposed_content(self) -> ProposalContent:
        """Parse and validate original_proposed_content JSON string, return typed Pydantic model.

        Returns:
            Typed Pydantic model instance matching the original proposal content structure.

        Raises:
            ValueError: If JSON is invalid or cannot be parsed into a valid ProposalContent model.
        """
        import json

        try:
            data = json.loads(self.original_proposed_content)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in original_proposed_content: {exc}") from exc

        # Use Pydantic's model_validate to parse based on command field
        command = data.get("command")
        if command == "UPDATE":
            if "achievement_id" in data:
                return AchievementUpdate.model_validate(data)
            elif self.proposal_type == ProposalType.role_overview_update:
                return RoleOverviewUpdate.model_validate(data)
            elif self.proposal_type == ProposalType.company_overview_update:
                return CompanyOverviewUpdate.model_validate(data)
        elif command == "ADD":
            if "title" in data:
                return AchievementAdd.model_validate(data)
            elif "skills" in data:
                return SkillAdd.model_validate(data)
        elif command == "DELETE":
            if "achievement_id" in data:
                return AchievementDelete.model_validate(data)
            elif "skills" in data:
                return SkillDelete.model_validate(data)

        # Fallback: try to validate against proposal_type
        if self.proposal_type == ProposalType.role_overview_update:
            return RoleOverviewUpdate.model_validate(data)
        elif self.proposal_type == ProposalType.company_overview_update:
            return CompanyOverviewUpdate.model_validate(data)
        elif self.proposal_type == ProposalType.skill_add:
            return SkillAdd.model_validate(data)
        elif self.proposal_type == ProposalType.skill_delete:
            return SkillDelete.model_validate(data)
        elif self.proposal_type == ProposalType.achievement_add:
            return AchievementAdd.model_validate(data)
        elif self.proposal_type == ProposalType.achievement_update:
            return AchievementUpdate.model_validate(data)
        elif self.proposal_type == ProposalType.achievement_delete:
            return AchievementDelete.model_validate(data)

        raise ValueError(f"Unable to parse original_proposed_content for proposal_type {self.proposal_type}")

    @staticmethod
    def serialize_proposed_content(content: ProposalContent) -> str:
        """Serialize Pydantic model to JSON string for database storage.

        Args:
            content: Pydantic model instance to serialize.

        Returns:
            JSON string representation of the model.

        Raises:
            ValueError: If content cannot be serialized to JSON.
        """
        import json

        try:
            return json.dumps(content.model_dump())
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Cannot serialize proposal content to JSON: {exc}") from exc


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

    def migrate_schema(self) -> None:
        """Apply schema migrations to add new tables and columns.

        This method ensures the database schema is up to date with the current models.
        Handles Sprint 010 migrations:
        - Creates Achievement table if it doesn't exist
        - Adds company_overview, role_overview, skills columns to Experience if missing
        - Adds title column to Achievement if missing
        Handles Sprint 014 migrations:
        - Creates ExperienceProposal table if it doesn't exist

        For SQLite, we use ALTER TABLE to add columns when safe.
        If migration fails, use reset_database() in development.
        """
        with self.get_session() as session:
            # Check existing tables before migration
            inspector = inspect(self.engine)
            tables_before = set(inspector.get_table_names())

            # First, create any new tables (Achievement, ExperienceProposal, etc.)
            # SQLModel's create_all() safely checks if tables exist and only creates missing ones
            SQLModel.metadata.create_all(self.engine)

            # Verify ExperienceProposal table was created if it didn't exist
            table_name = "experienceproposal"  # SQLModel converts ExperienceProposal to lowercase
            tables_after = set(inspector.get_table_names())
            if table_name.lower() in tables_after and table_name.lower() not in tables_before:
                logger.info(f"Created new table '{table_name}' during migration")
                # Verify table structure
                result = session.exec(text(f"PRAGMA table_info({table_name})"))
                columns = {row[1] for row in result}  # row[1] is the column name
                expected_columns = {
                    "id",
                    "session_id",
                    "proposal_type",
                    "experience_id",
                    "achievement_id",
                    "proposed_content",
                    "original_proposed_content",
                    "status",
                    "created_at",
                    "updated_at",
                }
                if columns == expected_columns:
                    logger.info(f"Verified '{table_name}' table structure: all expected columns present")
                else:
                    missing = expected_columns - columns
                    if missing:
                        logger.warning(f"'{table_name}' table is missing columns: {missing}")
            elif table_name.lower() in tables_after:
                logger.info(f"Table '{table_name}' already exists, skipping creation")

            # Check if Experience table needs new columns
            # SQLite-specific: Check if columns exist by querying pragma
            try:
                result = session.exec(text("PRAGMA table_info(experience)"))
                columns = {row[1] for row in result}  # row[1] is the column name

                # Add company_overview if missing
                if "company_overview" not in columns:
                    session.exec(text("ALTER TABLE experience ADD COLUMN company_overview TEXT"))
                    logger.info("Added company_overview column to experience table")

                # Add role_overview if missing
                if "role_overview" not in columns:
                    session.exec(text("ALTER TABLE experience ADD COLUMN role_overview TEXT"))
                    logger.info("Added role_overview column to experience table")

                # Add skills if missing (stored as JSON)
                if "skills" not in columns:
                    session.exec(text("ALTER TABLE experience ADD COLUMN skills JSON"))
                    logger.info("Added skills column to experience table")

                # Check if Achievement table needs title column
                result = session.exec(text("PRAGMA table_info(achievement)"))
                achievement_columns = {row[1] for row in result}  # row[1] is the column name

                # Add title if missing
                if "title" not in achievement_columns:
                    # For SQLite, we need to set a default value since the column is NOT NULL
                    # We'll use a placeholder title for existing records
                    session.exec(text("ALTER TABLE achievement ADD COLUMN title TEXT DEFAULT 'Achievement'"))
                    logger.info("Added title column to achievement table")

                session.commit()
                logger.info("Database schema migration completed successfully")

            except Exception as e:
                logger.exception("Error during schema migration", exception=e)
                session.rollback()
                raise

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

    # Achievement methods
    def add_achievement(self, achievement: Achievement) -> int:
        """Add a new achievement to the database."""
        with self.get_session() as session:
            _set_timestamps_on_create(achievement)

            session.add(achievement)
            session.commit()
            session.refresh(achievement)
            logger.info(f"Added achievement (ID: {achievement.id}) to experience {achievement.experience_id}")
            return achievement.id

    def get_achievement(self, achievement_id: int) -> Achievement | None:
        """Get an achievement by ID."""
        with self.get_session() as session:
            return session.get(Achievement, achievement_id)

    def list_experience_achievements(self, experience_id: int) -> list[Achievement]:
        """Get all achievements for an experience, ordered by order field."""
        with self.get_session() as session:
            statement = (
                select(Achievement).where(Achievement.experience_id == experience_id).order_by(Achievement.order.asc())
            )
            return list(session.exec(statement))

    def update_achievement(self, achievement_id: int, **updates) -> Achievement | None:
        """Update an achievement by ID."""
        with self.get_session() as session:
            achievement = session.get(Achievement, achievement_id)
            if achievement:
                for key, value in updates.items():
                    setattr(achievement, key, value)
                _touch_updated_at(achievement)
                session.add(achievement)
                session.commit()
                session.refresh(achievement)
                logger.info(f"Updated achievement {achievement_id}")
            return achievement

    def delete_achievement(self, achievement_id: int) -> bool:
        """Delete an achievement by ID."""
        with self.get_session() as session:
            achievement = session.get(Achievement, achievement_id)
            if achievement:
                session.delete(achievement)
                session.commit()
                logger.info(f"Deleted achievement {achievement_id}")
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

    # ExperienceProposal methods
    def add_experience_proposal(self, proposal: ExperienceProposal) -> int:
        """Validate a new experience proposal (read-only validation only - does not execute insert).

        Args:
            proposal: The ExperienceProposal object to validate.

        Returns:
            Would return the proposal ID if insert were executed (currently returns 0 for validation).

        Note:
            This method only validates the proposal object structure and required fields.
            Database insert is NOT executed per database safety constraints.
        """
        # Validate proposal object structure
        if not isinstance(proposal, ExperienceProposal):
            raise ValueError("proposal must be an ExperienceProposal instance")

        # Validate required fields
        if not proposal.session_id:
            raise ValueError("session_id is required")
        if not proposal.experience_id:
            raise ValueError("experience_id is required")
        if not proposal.proposal_type:
            raise ValueError("proposal_type is required")
        if not proposal.proposed_content:
            raise ValueError("proposed_content is required")
        if not proposal.original_proposed_content:
            raise ValueError("original_proposed_content is required")
        if not proposal.status:
            raise ValueError("status is required")

        # Validate proposal_type enum
        if proposal.proposal_type not in ProposalType:
            raise ValueError(f"Invalid proposal_type: {proposal.proposal_type}")

        # Validate status enum
        if proposal.status not in ProposalStatus:
            raise ValueError(f"Invalid status: {proposal.status}")

        # Validate achievement_id is provided when required
        if proposal.proposal_type in (ProposalType.achievement_update, ProposalType.achievement_delete):
            if not proposal.achievement_id:
                raise ValueError("achievement_id is required for achievement_update and achievement_delete proposals")

        # Validate JSON content
        import json

        try:
            json.loads(proposal.proposed_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"proposed_content must be valid JSON: {e}")

        try:
            json.loads(proposal.original_proposed_content)
        except json.JSONDecodeError as e:
            raise ValueError(f"original_proposed_content must be valid JSON: {e}")

        # Validate foreign key references exist (read-only check)
        with self.get_session() as session:
            session_obj = session.get(JobIntakeSession, proposal.session_id)
            if not session_obj:
                raise ValueError(f"session_id {proposal.session_id} does not exist")

            experience_obj = session.get(Experience, proposal.experience_id)
            if not experience_obj:
                raise ValueError(f"experience_id {proposal.experience_id} does not exist")

            if proposal.achievement_id:
                achievement_obj = session.get(Achievement, proposal.achievement_id)
                if not achievement_obj:
                    raise ValueError(f"achievement_id {proposal.achievement_id} does not exist")

        logger.info(
            f"Validated experience proposal: type={proposal.proposal_type}, "
            f"experience_id={proposal.experience_id}, session_id={proposal.session_id}"
        )
        # Return 0 as placeholder since we're not actually inserting
        return 0

    def get_experience_proposal(self, proposal_id: int) -> ExperienceProposal | None:
        """Get an experience proposal by ID (read-only - safe to test)."""
        with self.get_session() as session:
            return session.get(ExperienceProposal, proposal_id)

    def list_session_proposals(self, session_id: int) -> list[ExperienceProposal]:
        """Get all proposals for a session (read-only - safe to test).

        Args:
            session_id: The job intake session ID.

        Returns:
            A list of ExperienceProposal records for the session, ordered by created_at desc.
        """
        with self.get_session() as session:
            statement = (
                select(ExperienceProposal)
                .where(ExperienceProposal.session_id == session_id)
                .order_by(ExperienceProposal.created_at.desc())
            )
            return list(session.exec(statement))

    def update_experience_proposal(self, proposal_id: int, **updates) -> ExperienceProposal | None:
        """Validate updates to an experience proposal (read-only validation only - does not execute update).

        Args:
            proposal_id: The ID of the proposal to update.
            **updates: Dictionary of field names and values to update.

        Returns:
            Would return the updated proposal if update were executed (currently returns None for validation).

        Note:
            This method only validates the update fields and checks that the proposal exists.
            Database update is NOT executed per database safety constraints.
        """
        with self.get_session() as session:
            proposal = session.get(ExperienceProposal, proposal_id)
            if not proposal:
                logger.warning(f"Experience proposal {proposal_id} not found")
                return None

            # Validate update fields
            valid_fields = {
                "session_id",
                "proposal_type",
                "experience_id",
                "achievement_id",
                "proposed_content",
                "original_proposed_content",
                "status",
            }

            for key, value in updates.items():
                if key not in valid_fields:
                    raise ValueError(f"Invalid field for update: {key}")

                # Validate enum fields
                if key == "proposal_type" and value not in ProposalType:
                    raise ValueError(f"Invalid proposal_type: {value}")

                if key == "status" and value not in ProposalStatus:
                    raise ValueError(f"Invalid status: {value}")

                # Validate JSON content fields
                if key in ("proposed_content", "original_proposed_content"):
                    import json

                    try:
                        json.loads(value)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"{key} must be valid JSON: {e}")

                # Validate foreign key references if updated
                if key == "session_id":
                    session_obj = session.get(JobIntakeSession, value)
                    if not session_obj:
                        raise ValueError(f"session_id {value} does not exist")

                if key == "experience_id":
                    experience_obj = session.get(Experience, value)
                    if not experience_obj:
                        raise ValueError(f"experience_id {value} does not exist")

                if key == "achievement_id" and value is not None:
                    achievement_obj = session.get(Achievement, value)
                    if not achievement_obj:
                        raise ValueError(f"achievement_id {value} does not exist")

            logger.info(f"Validated updates for experience proposal {proposal_id}: {list(updates.keys())}")
            # Return None as placeholder since we're not actually updating
            return None

    def delete_experience_proposal(self, proposal_id: int) -> bool:
        """Validate deletion of an experience proposal (read-only validation only - does not execute delete).

        Args:
            proposal_id: The ID of the proposal to delete.

        Returns:
            Would return True if delete were executed (currently returns False for validation).

        Note:
            This method only validates that the proposal exists.
            Database delete is NOT executed per database safety constraints.
        """
        with self.get_session() as session:
            proposal = session.get(ExperienceProposal, proposal_id)
            if not proposal:
                logger.warning(f"Experience proposal {proposal_id} not found")
                return False

            logger.info(f"Validated deletion for experience proposal {proposal_id}")
            # Return False as placeholder since we're not actually deleting
            return False


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
