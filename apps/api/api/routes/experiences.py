"""Experience management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from api.dependencies import DBSession
from api.schemas.experience import (
    AchievementCreate,
    AchievementResponse,
    AchievementUpdate,
    ExperienceCreate,
    ExperienceResponse,
    ExperienceUpdate,
    ProposalCreate,
    ProposalResponse,
    ProposalUpdate,
)
from api.services.experience_service import ExperienceService
from api.services.job_intake_service.service import JobIntakeService
from api.utils.errors import NotFoundError
from src.database import ProposalStatus, db_manager

router = APIRouter()


@router.get("/experiences", response_model=list[ExperienceResponse])
async def list_experiences(user_id: int = Query(..., description="User ID"), session: DBSession = None) -> list[ExperienceResponse]:  # noqa: ARG001
    """List all experiences for a user."""
    experiences = ExperienceService.list_user_experiences(user_id)
    return [ExperienceResponse.model_validate(exp) for exp in experiences]


@router.get("/experiences/{experience_id}", response_model=ExperienceResponse)
async def get_experience(experience_id: int, session: DBSession) -> ExperienceResponse:
    """Get a specific experience."""
    experience = ExperienceService.get_experience(experience_id)
    if not experience:
        raise NotFoundError("Experience", experience_id)
    return ExperienceResponse.model_validate(experience)


@router.post("/experiences", response_model=ExperienceResponse, status_code=status.HTTP_201_CREATED)
async def create_experience(
    experience_data: ExperienceCreate,
    user_id: int = Query(..., description="User ID"),
    session: DBSession = None,  # noqa: ARG001
) -> ExperienceResponse:
    """Create a new experience."""
    experience_id = ExperienceService.create_experience(user_id, **experience_data.model_dump())
    experience = ExperienceService.get_experience(experience_id)
    if not experience:
        raise ValueError("Failed to create experience")
    return ExperienceResponse.model_validate(experience)


@router.patch("/experiences/{experience_id}", response_model=ExperienceResponse)
async def update_experience(experience_id: int, experience_data: ExperienceUpdate, session: DBSession) -> ExperienceResponse:
    """Update an experience."""
    updates = experience_data.model_dump(exclude_unset=True)
    experience = ExperienceService.update_experience(experience_id, **updates)
    if not experience:
        raise NotFoundError("Experience", experience_id)
    return ExperienceResponse.model_validate(experience)


@router.delete("/experiences/{experience_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experience(experience_id: int, session: DBSession) -> None:
    """Delete an experience."""
    deleted = ExperienceService.delete_experience(experience_id)
    if not deleted:
        raise NotFoundError("Experience", experience_id)


@router.get("/experiences/{experience_id}/achievements", response_model=list[AchievementResponse])
async def list_achievements(experience_id: int, session: DBSession) -> list[AchievementResponse]:
    """List all achievements for an experience."""
    achievements = db_manager.list_experience_achievements(experience_id)
    return [AchievementResponse.model_validate(ach) for ach in achievements]


@router.post("/experiences/{experience_id}/achievements", response_model=AchievementResponse, status_code=status.HTTP_201_CREATED)
async def create_achievement(
    experience_id: int,
    achievement_data: AchievementCreate,
    session: DBSession = None,  # noqa: ARG001
) -> AchievementResponse:
    """Create a new achievement."""
    achievement_id = ExperienceService.add_achievement(
        experience_id,
        title=achievement_data.title,
        content=achievement_data.content,
        order=achievement_data.order,
    )
    achievement = db_manager.get_achievement(achievement_id)
    if not achievement:
        raise ValueError("Failed to create achievement")
    return AchievementResponse.model_validate(achievement)


@router.patch("/achievements/{achievement_id}", response_model=AchievementResponse)
async def update_achievement(achievement_id: int, achievement_data: AchievementUpdate, session: DBSession = None) -> AchievementResponse:  # noqa: ARG001
    """Update an achievement."""
    if achievement_data.title is None or achievement_data.content is None:
        raise ValueError("Title and content are required")
    achievement = ExperienceService.update_achievement(achievement_id, achievement_data.title, achievement_data.content)
    if not achievement:
        raise NotFoundError("Achievement", achievement_id)
    return AchievementResponse.model_validate(achievement)


@router.delete("/achievements/{achievement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_achievement(achievement_id: int, session: DBSession = None) -> None:  # noqa: ARG001
    """Delete an achievement."""
    deleted = ExperienceService.delete_achievement(achievement_id)
    if not deleted:
        raise NotFoundError("Achievement", achievement_id)


@router.get("/experiences/{experience_id}/proposals", response_model=list[ProposalResponse])
async def list_proposals(experience_id: int, session_id: int = Query(..., description="Session ID"), session: DBSession = None) -> list[ProposalResponse]:  # noqa: ARG001
    """List all proposals for an experience."""
    proposals = db_manager.list_session_proposals(session_id)
    # Filter by experience_id
    proposals = [p for p in proposals if p.experience_id == experience_id]
    return [ProposalResponse.model_validate(p) for p in proposals]


@router.post("/experiences/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
async def create_proposal(proposal_data: ProposalCreate, session: DBSession = None) -> ProposalResponse:  # noqa: ARG001
    """Create a new proposal."""
    from src.database import ExperienceProposal

    proposal = ExperienceProposal(
        session_id=proposal_data.session_id,
        proposal_type=proposal_data.proposal_type,
        experience_id=proposal_data.experience_id,
        achievement_id=proposal_data.achievement_id,
        proposed_content=proposal_data.proposed_content,
        original_proposed_content=proposal_data.original_proposed_content,
        status=proposal_data.status,
    )
    proposal_id = db_manager.add_experience_proposal(proposal)
    created_proposal = db_manager.get_experience_proposal(proposal_id)
    if not created_proposal:
        raise ValueError("Failed to create proposal")
    return ProposalResponse.model_validate(created_proposal)


@router.patch("/proposals/{proposal_id}/accept", response_model=ProposalResponse)
async def accept_proposal(proposal_id: int, session: DBSession = None) -> ProposalResponse:  # noqa: ARG001
    """Accept a proposal."""
    # Accept proposal (validates only in development mode)
    success = JobIntakeService.accept_proposal(proposal_id)
    if not success:
        raise ValueError("Failed to accept proposal")

    # Update proposal status
    proposal = db_manager.get_experience_proposal(proposal_id)
    if not proposal:
        raise NotFoundError("Proposal", proposal_id)

    updated = db_manager.update_experience_proposal(proposal_id, status=ProposalStatus.accepted)
    if not updated:
        raise NotFoundError("Proposal", proposal_id)
    return ProposalResponse.model_validate(updated)


@router.patch("/proposals/{proposal_id}/reject", response_model=ProposalResponse)
async def reject_proposal(proposal_id: int, session: DBSession = None) -> ProposalResponse:  # noqa: ARG001
    """Reject a proposal."""
    proposal = db_manager.get_experience_proposal(proposal_id)
    if not proposal:
        raise NotFoundError("Proposal", proposal_id)

    updated = db_manager.update_experience_proposal(proposal_id, status=ProposalStatus.rejected)
    if not updated:
        raise NotFoundError("Proposal", proposal_id)
    return ProposalResponse.model_validate(updated)


@router.delete("/proposals/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_proposal(proposal_id: int, session: DBSession = None) -> None:  # noqa: ARG001
    """Delete a proposal."""
    proposal = db_manager.get_experience_proposal(proposal_id)
    if not proposal:
        raise NotFoundError("Proposal", proposal_id)
    # Note: db_manager doesn't have delete_proposal, but we can add it if needed
    # For now, mark as rejected
    db_manager.update_experience_proposal(proposal_id, status=ProposalStatus.rejected)

