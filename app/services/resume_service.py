"""Service for resume generation operations."""

from src.agents.main import create_experience
from src.database import Experience as DbExperience
from src.generate_resume import generate_resume as run_workflow
from src.logging_config import logger


class ResumeService:
    """Service class for resume-related operations."""

    @staticmethod
    def generate_resume(
        job_description: str, experiences: list[DbExperience], responses: str = "", user_id: int | None = None
    ) -> str:
        """Generate a resume using the LangGraph workflow."""
        logger.info(
            f"Generating resume for user {user_id} with job description length={len(job_description)} and experiences={len(experiences) if experiences else 0}"
        )

        try:
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

            # Run the workflow
            response = run_workflow(job_description, agent_experiences, responses or "")

            logger.info("Resume generation completed successfully")
            return response

        except Exception as e:
            logger.exception(e)
            return f"Error generating resume: {str(e)}"
