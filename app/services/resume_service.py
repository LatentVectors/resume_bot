"""Service for resume generation operations."""

from loguru import logger

from src.generate_resume import generate_resume


class ResumeService:
    """Service class for resume-related operations."""

    @staticmethod
    def generate_resume(user_input: str, user_id: int | None = None) -> str:
        """Generate a resume using the LangGraph workflow."""
        logger.info(f"Generating resume for user {user_id} with input: {user_input}")

        try:
            # Run the workflow
            response = generate_resume(user_input)

            logger.info("Resume generation completed successfully")
            return response

        except Exception as e:
            logger.error(f"Error generating resume: {e}")
            return f"Error generating resume: {str(e)}"
