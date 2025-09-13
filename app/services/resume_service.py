"""Service for resume generation operations."""

from src.agents.main import create_experience
from src.config import settings
from src.database import Education as DbEducation
from src.database import Experience as DbExperience
from src.database import Job as DbJob
from src.database import User as DbUser
from src.database import db_manager
from src.generate_resume import generate_resume as run_workflow
from src.logging_config import logger


class ResumeService:
    """Service class for resume-related operations."""

    @staticmethod
    def generate_resume(
        job_description: str, experiences: list[DbExperience], responses: str = "", user_id: int | None = None
    ) -> DbJob:
        """Generate a PDF resume via agent workflow and create a Job record.

        Returns:
            DbJob: Persisted Job record containing the generated resume filename.

        Raises:
            ValueError: If required inputs are missing (e.g., user_id).
            Exception: For failures during generation or database operations.
        """
        logger.info(
            f"Generating resume for user {user_id} with job description length={len(job_description)} and experiences={len(experiences) if experiences else 0}"
        )

        if not user_id or not isinstance(user_id, int) or user_id <= 0:
            raise ValueError("user_id is required to create a Job record")

        resume_filename: str | None = None

        try:
            # Fetch user and education data
            user: DbUser | None = db_manager.get_user(user_id)
            educations: list[DbEducation] = db_manager.list_user_educations(user_id)

            # Convert DB experiences to agent experiences
            agent_experiences = [
                create_experience(
                    id=str(exp.id) if exp.id is not None else "",
                    company=exp.company_name,
                    title=exp.job_title,
                    start_date=exp.start_date,
                    end_date=exp.end_date,
                    content=exp.content,
                    points=[],
                )
                for exp in (experiences or [])
            ]

            # Prepare user info fields
            user_name = f"{user.first_name} {user.last_name}" if user else ""
            user_email = user.email if user and user.email else ""
            user_phone = user.phone_number if user else None
            user_linkedin_url = user.linkedin_url if user else None
            user_education = (
                [
                    {
                        "school": edu.school,
                        "degree": edu.degree,
                        "start_date": edu.start_date,
                        "end_date": edu.end_date,
                    }
                    for edu in educations
                ]
                if educations
                else None
            )

            # Run the workflow (returns PDF filename)
            resume_filename = run_workflow(
                job_description,
                agent_experiences,
                responses or "",
                user_name=user_name,
                user_email=user_email,
                user_phone=user_phone,
                user_linkedin_url=user_linkedin_url,
                user_education=user_education,
            )

            if not resume_filename or not isinstance(resume_filename, str):
                raise RuntimeError("Resume generation returned no filename")

            # Create Job record
            job = DbJob(
                user_id=user_id,
                job_description=job_description,
                company_name=None,
                job_title=None,
                resume_filename=resume_filename,
            )
            db_manager.add_job(job)

            logger.info("Resume generation completed and Job record created successfully")
            return job

        except Exception as e:
            logger.exception(e)

            # Cleanup orphaned PDF file if it was generated but DB failed
            try:
                if resume_filename:
                    output_path = (settings.data_dir / "resumes" / resume_filename).resolve()
                    if output_path.exists():
                        output_path.unlink(missing_ok=True)  # type: ignore[arg-type]
                        logger.info(f"Cleaned up orphaned resume file: {output_path}")
            except Exception as cleanup_err:  # noqa: BLE001
                logger.error(f"Failed to cleanup resume file '{resume_filename}': {cleanup_err}", exception=True)

            # Re-raise so callers can handle appropriately
            raise
