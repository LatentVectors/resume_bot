"""Database models and connection management using SQLModel."""

from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from sqlmodel import Field, Session, SQLModel, create_engine, select

from src.logging_config import logger

from .config import settings


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
    start_date: date  # ISO date format (YYYY-MM-DD)
    end_date: date | None = Field(default=None)  # ISO date format (YYYY-MM-DD)
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Education(SQLModel, table=True):
    """Education model for education entries."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    school: str
    degree: str
    start_date: date  # ISO date format (YYYY-MM-DD)
    end_date: date  # ISO date format (YYYY-MM-DD)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Job(SQLModel, table=True):
    """Job application model for tracking resumes generated for specific jobs."""

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    job_description: str
    company_name: str | None = Field(default=None)
    job_title: str | None = Field(default=None)
    resume_filename: str
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
            # Set timestamps if not already set
            if not user.created_at:
                user.created_at = datetime.now()
            if not user.updated_at:
                user.updated_at = datetime.now()

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
                # Always update the updated_at timestamp
                user.updated_at = datetime.now()
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
            # Set timestamps if not already set
            if not experience.created_at:
                experience.created_at = datetime.now()
            if not experience.updated_at:
                experience.updated_at = datetime.now()

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
                # Always update the updated_at timestamp
                experience.updated_at = datetime.now()
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

    # Education methods
    def add_education(self, education: Education) -> int:
        """Add a new education to the database."""
        with self.get_session() as session:
            # Set timestamps if not already set
            if not education.created_at:
                education.created_at = datetime.now()
            if not education.updated_at:
                education.updated_at = datetime.now()

            session.add(education)
            session.commit()
            session.refresh(education)
            logger.info(f"Added education: {education.degree} at {education.school} (ID: {education.id})")
            return education.id

    def get_education(self, education_id: int) -> Education | None:
        """Get an education by ID."""
        with self.get_session() as session:
            return session.get(Education, education_id)

    def list_user_educations(self, user_id: int) -> list[Education]:
        """Get all educations for a user."""
        with self.get_session() as session:
            statement = select(Education).where(Education.user_id == user_id).order_by(Education.start_date.desc())
            return list(session.exec(statement))

    def update_education(self, education_id: int, **updates) -> Education | None:
        """Update an education by ID."""
        with self.get_session() as session:
            education = session.get(Education, education_id)
            if education:
                for key, value in updates.items():
                    setattr(education, key, value)
                # Always update the updated_at timestamp
                education.updated_at = datetime.now()
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
            if not job.created_at:
                job.created_at = datetime.now()
            if not job.updated_at:
                job.updated_at = datetime.now()

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
                job.updated_at = datetime.now()
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


# Global database manager instance
db_manager = DatabaseManager()
