"""API client for experience endpoints with typed responses."""

from api.schemas.experience import (
    AchievementCreate,
    AchievementResponse,
    AchievementUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    ProposalCreate,
    ProposalResponse,
)
from app.api_client.client import api_client
from src.database import ProposalStatus, ProposalType


class ExperiencesAPI:
    """API client for experience endpoints with typed responses."""

    @staticmethod
    async def list_experiences(user_id: int) -> list[ExperienceResponse]:
        """List all experiences for a user. Returns list of ExperienceResponse models."""
        return await api_client.get(
            "/api/v1/experiences",
            params={"user_id": user_id},
            response_model=ExperienceResponse,
        )

    @staticmethod
    async def get_experience(experience_id: int) -> ExperienceResponse:
        """Get a specific experience. Returns ExperienceResponse model."""
        return await api_client.get(
            f"/api/v1/experiences/{experience_id}",
            response_model=ExperienceResponse,
        )

    @staticmethod
    async def create_experience(
        user_id: int,
        company_name: str,
        job_title: str,
        location: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        company_overview: str | None = None,
        role_overview: str | None = None,
        skills: list[str] | None = None,
    ) -> ExperienceResponse:
        """Create a new experience. Returns ExperienceResponse model."""
        return await api_client.post(
            "/api/v1/experiences",
            params={"user_id": user_id},
            json=ExperienceCreate(
                company_name=company_name,
                job_title=job_title,
                location=location,
                start_date=start_date,
                end_date=end_date,
                company_overview=company_overview,
                role_overview=role_overview,
                skills=skills or [],
            ).model_dump(),
            response_model=ExperienceResponse,
        )

    @staticmethod
    async def update_experience(
        experience_id: int,
        company_name: str | None = None,
        job_title: str | None = None,
        location: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        company_overview: str | None = None,
        role_overview: str | None = None,
        skills: list[str] | None = None,
    ) -> ExperienceResponse:
        """Update an experience. Returns ExperienceResponse model."""
        update_data = ExperienceUpdate(
            company_name=company_name,
            job_title=job_title,
            location=location,
            start_date=start_date,
            end_date=end_date,
            company_overview=company_overview,
            role_overview=role_overview,
            skills=skills,
        ).model_dump(exclude_unset=True)
        return await api_client.patch(
            f"/api/v1/experiences/{experience_id}",
            json=update_data,
            response_model=ExperienceResponse,
        )

    @staticmethod
    async def delete_experience(experience_id: int) -> None:
        """Delete an experience."""
        await api_client.delete(f"/api/v1/experiences/{experience_id}")

    @staticmethod
    async def list_achievements(experience_id: int) -> list[AchievementResponse]:
        """List all achievements for an experience. Returns list of AchievementResponse models."""
        return await api_client.get(
            f"/api/v1/experiences/{experience_id}/achievements",
            response_model=AchievementResponse,
        )

    @staticmethod
    async def create_achievement(
        experience_id: int,
        title: str,
        content: str,
        order: int = 0,
    ) -> AchievementResponse:
        """Create a new achievement. Returns AchievementResponse model."""
        return await api_client.post(
            f"/api/v1/experiences/{experience_id}/achievements",
            json=AchievementCreate(title=title, content=content, order=order).model_dump(),
            response_model=AchievementResponse,
        )

    @staticmethod
    async def update_achievement(
        achievement_id: int,
        title: str | None = None,
        content: str | None = None,
        order: int | None = None,
    ) -> AchievementResponse:
        """Update an achievement. Returns AchievementResponse model."""
        update_data = AchievementUpdate(
            title=title,
            content=content,
            order=order,
        ).model_dump(exclude_unset=True)
        return await api_client.patch(
            f"/api/v1/achievements/{achievement_id}",
            json=update_data,
            response_model=AchievementResponse,
        )

    @staticmethod
    async def delete_achievement(achievement_id: int) -> None:
        """Delete an achievement."""
        await api_client.delete(f"/api/v1/achievements/{achievement_id}")

    @staticmethod
    async def list_proposals(experience_id: int, session_id: int) -> list[ProposalResponse]:
        """List all proposals for an experience. Returns list of ProposalResponse models."""
        return await api_client.get(
            f"/api/v1/experiences/{experience_id}/proposals",
            params={"session_id": session_id},
            response_model=ProposalResponse,
        )

    @staticmethod
    async def create_proposal(
        session_id: int,
        proposal_type: ProposalType,
        experience_id: int,
        proposed_content: str,
        original_proposed_content: str,
        achievement_id: int | None = None,
        status: ProposalStatus = ProposalStatus.pending,
    ) -> ProposalResponse:
        """Create a new proposal. Returns ProposalResponse model."""
        return await api_client.post(
            "/api/v1/experiences/proposals",
            json=ProposalCreate(
                session_id=session_id,
                proposal_type=proposal_type,
                experience_id=experience_id,
                achievement_id=achievement_id,
                proposed_content=proposed_content,
                original_proposed_content=original_proposed_content,
                status=status,
            ).model_dump(),
            response_model=ProposalResponse,
        )

    @staticmethod
    async def accept_proposal(proposal_id: int) -> ProposalResponse:
        """Accept a proposal. Returns ProposalResponse model."""
        return await api_client.patch(
            f"/api/v1/proposals/{proposal_id}/accept",
            response_model=ProposalResponse,
        )

    @staticmethod
    async def reject_proposal(proposal_id: int) -> ProposalResponse:
        """Reject a proposal. Returns ProposalResponse model."""
        return await api_client.patch(
            f"/api/v1/proposals/{proposal_id}/reject",
            response_model=ProposalResponse,
        )

    @staticmethod
    async def delete_proposal(proposal_id: int) -> None:
        """Delete a proposal."""
        await api_client.delete(f"/api/v1/proposals/{proposal_id}")

