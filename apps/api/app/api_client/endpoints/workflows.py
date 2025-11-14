"""API client for workflow endpoints with typed responses."""

from app.api_client.client import api_client
from api.schemas.workflow import (
    ExperienceExtractionRequest,
    ExperienceExtractionResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    ResumeChatMessage,
    ResumeChatRequest,
    ResumeChatResponse,
    ResumeGenerationRequest,
    ResumeGenerationResponse,
    StakeholderAnalysisRequest,
    StakeholderAnalysisResponse,
)
from src.features.resume.types import ResumeData


class WorkflowsAPI:
    """API client for workflow endpoints with typed responses."""

    @staticmethod
    async def gap_analysis(
        job_description: str,
        experience_ids: list[int],
    ) -> GapAnalysisResponse:
        """Run gap analysis workflow. Returns GapAnalysisResponse model."""
        return await api_client.post(
            "/api/v1/workflows/gap-analysis",
            json=GapAnalysisRequest(
                job_description=job_description,
                experience_ids=experience_ids,
            ).model_dump(),
            response_model=GapAnalysisResponse,
        )

    @staticmethod
    async def stakeholder_analysis(
        job_description: str,
        experience_ids: list[int],
    ) -> StakeholderAnalysisResponse:
        """Run stakeholder analysis workflow. Returns StakeholderAnalysisResponse model."""
        return await api_client.post(
            "/api/v1/workflows/stakeholder-analysis",
            json=StakeholderAnalysisRequest(
                job_description=job_description,
                experience_ids=experience_ids,
            ).model_dump(),
            response_model=StakeholderAnalysisResponse,
        )

    @staticmethod
    async def experience_extraction(
        chat_messages: list[dict[str, str]],
        experience_ids: list[int],
    ) -> ExperienceExtractionResponse:
        """Extract experience updates from conversation. Returns ExperienceExtractionResponse model."""
        return await api_client.post(
            "/api/v1/workflows/experience-extraction",
            json=ExperienceExtractionRequest(
                chat_messages=chat_messages,
                experience_ids=experience_ids,
            ).model_dump(),
            response_model=ExperienceExtractionResponse,
        )

    @staticmethod
    async def resume_chat(
        messages: list[ResumeChatMessage],
        job_id: int,
        gap_analysis: str,
        stakeholder_analysis: str,
        work_experience: str,
        selected_version_id: int | None = None,
    ) -> ResumeChatResponse:
        """Run resume refinement chat workflow. Returns ResumeChatResponse model."""
        # Convert ResumeChatMessage objects to dicts
        message_dicts = [msg.model_dump() for msg in messages]
        return await api_client.post(
            "/api/v1/workflows/resume-chat",
            json=ResumeChatRequest(
                messages=message_dicts,
                job_id=job_id,
                selected_version_id=selected_version_id,
                gap_analysis=gap_analysis,
                stakeholder_analysis=stakeholder_analysis,
                work_experience=work_experience,
            ).model_dump(),
            response_model=ResumeChatResponse,
        )

    @staticmethod
    async def resume_generation(
        user_id: int,
        job_description: str,
        resume_draft: ResumeData | None = None,
        special_instructions: str | None = None,
    ) -> ResumeGenerationResponse:
        """Generate resume using LangGraph agent. Returns ResumeGenerationResponse model."""
        return await api_client.post(
            "/api/v1/workflows/resume-generation",
            params={"user_id": user_id},
            json=ResumeGenerationRequest(
                job_description=job_description,
                experiences=[],  # Not used - service fetches from DB
                responses="",
                special_instructions=special_instructions,
                resume_draft=resume_draft,
            ).model_dump(exclude={"experiences", "responses"}),
            response_model=ResumeGenerationResponse,
        )

