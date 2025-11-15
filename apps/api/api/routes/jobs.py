"""Job management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from api.dependencies import DBSession
from api.schemas.job import BulkDeleteRequest, BulkDeleteResponse, JobCreate, JobResponse, JobsListResponse, JobUpdate
from api.services.job_service import JobService
from api.utils.errors import NotFoundError
from src.database import JobStatus

router = APIRouter()


@router.get("/jobs", response_model=JobsListResponse)
async def list_jobs(
    user_id: int = Query(..., description="User ID"),
    status_filter: JobStatus | None = Query(None, description="Filter by status"),
    favorite_only: bool = Query(False, description="Show only favorites"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Maximum number of records to return"),
    session: DBSession = None,  # noqa: ARG001
) -> JobsListResponse:
    """List jobs for a user with pagination."""
    statuses = [status_filter] if status_filter else None
    jobs, total = JobService.list_jobs(
        user_id=user_id, statuses=statuses, favorites_only=favorite_only, skip=skip, limit=limit
    )
    return JobsListResponse(
        items=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, session: DBSession) -> JobResponse:
    """Get a specific job."""
    job = JobService.get_job(job_id)
    if not job:
        raise NotFoundError("Job", job_id)
    return JobResponse.model_validate(job)


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(job_data: JobCreate, user_id: int = Query(..., description="User ID"), session: DBSession = None) -> JobResponse:  # noqa: ARG001
    """Create a new job."""
    job = JobService.save_job(
        user_id=user_id,
        title=job_data.title or "",
        company=job_data.company or "",
        description=job_data.description,
        favorite=job_data.favorite,
    )
    return JobResponse.model_validate(job)


@router.patch("/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: int, job_data: JobUpdate, session: DBSession) -> JobResponse:
    """Update a job."""
    updates = {}
    if job_data.title is not None:
        updates["title"] = job_data.title
    if job_data.company is not None:
        updates["company"] = job_data.company
    if job_data.description is not None:
        updates["job_description"] = job_data.description
    if job_data.favorite is not None:
        updates["is_favorite"] = job_data.favorite

    job = JobService.update_job_fields(job_id, **updates)
    if not job:
        raise NotFoundError("Job", job_id)

    # Handle status update separately if provided
    if job_data.status is not None:
        job = JobService.set_status(job_id, job_data.status)
        if not job:
            raise NotFoundError("Job", job_id)

    return JobResponse.model_validate(job)


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(job_id: int, session: DBSession) -> None:
    """Delete a job."""
    deleted = JobService.delete_job(job_id)
    if not deleted:
        raise NotFoundError("Job", job_id)


@router.patch("/jobs/{job_id}/favorite", response_model=JobResponse)
async def toggle_favorite(job_id: int, favorite: bool = Query(..., description="Favorite status"), session: DBSession = None) -> JobResponse:  # noqa: ARG001
    """Toggle favorite status for a job."""
    job = JobService.update_job_fields(job_id, is_favorite=favorite)
    if not job:
        raise NotFoundError("Job", job_id)
    return JobResponse.model_validate(job)


@router.patch("/jobs/{job_id}/status", response_model=JobResponse)
async def update_status(
    job_id: int,
    status: JobStatus = Query(..., description="New status"),
    session: DBSession = None,  # noqa: ARG001
) -> JobResponse:
    """Update job status."""
    job = JobService.set_status(job_id, status)
    if not job:
        raise NotFoundError("Job", job_id)
    return JobResponse.model_validate(job)


@router.post("/jobs/{job_id}/apply", response_model=JobResponse)
async def mark_as_applied(job_id: int, session: DBSession = None) -> JobResponse:  # noqa: ARG001
    """Mark a job as applied."""
    job = JobService.set_status(job_id, "Applied")
    if not job:
        raise NotFoundError("Job", job_id)
    return JobResponse.model_validate(job)


@router.get("/jobs/{job_id}/intake-session", response_model=dict)
async def get_intake_session(job_id: int, session: DBSession) -> dict:
    """Get intake session for a job."""
    intake_session = JobService.get_intake_session(job_id)
    if not intake_session:
        raise NotFoundError("IntakeSession", job_id)
    return {
        "id": intake_session.id,
        "job_id": intake_session.job_id,
        "current_step": intake_session.current_step,
        "step1_completed": intake_session.step1_completed,
        "step2_completed": intake_session.step2_completed,
        "step3_completed": intake_session.step3_completed,
        "gap_analysis": intake_session.gap_analysis,
        "stakeholder_analysis": intake_session.stakeholder_analysis,
        "created_at": intake_session.created_at.isoformat() if intake_session.created_at else None,
        "updated_at": intake_session.updated_at.isoformat() if intake_session.updated_at else None,
        "completed_at": intake_session.completed_at.isoformat() if intake_session.completed_at else None,
    }


@router.post("/jobs/{job_id}/intake-session", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_intake_session(job_id: int, session: DBSession) -> dict:
    """Create intake session for a job."""
    intake_session = JobService.create_intake_session(job_id)
    return {
        "id": intake_session.id,
        "job_id": intake_session.job_id,
        "current_step": intake_session.current_step,
        "step1_completed": intake_session.step1_completed,
        "step2_completed": intake_session.step2_completed,
        "step3_completed": intake_session.step3_completed,
        "gap_analysis": intake_session.gap_analysis,
        "stakeholder_analysis": intake_session.stakeholder_analysis,
        "created_at": intake_session.created_at.isoformat() if intake_session.created_at else None,
        "updated_at": intake_session.updated_at.isoformat() if intake_session.updated_at else None,
        "completed_at": intake_session.completed_at.isoformat() if intake_session.completed_at else None,
    }


@router.patch("/jobs/{job_id}/intake-session", response_model=dict)
async def update_intake_session(
    job_id: int,
    current_step: int | None = Query(None, description="Current step (1-3)"),
    step_completed: int | None = Query(None, description="Step to mark as completed (1-3)"),
    gap_analysis: str | None = Query(None, description="Gap analysis text"),
    stakeholder_analysis: str | None = Query(None, description="Stakeholder analysis text"),
    session: DBSession = None,  # noqa: ARG001
) -> dict:
    """Update intake session for a job."""
    intake_session = JobService.get_intake_session(job_id)
    if not intake_session:
        raise NotFoundError("IntakeSession", job_id)

    if current_step is not None:
        completed = step_completed == current_step if step_completed is not None else False
        updated = JobService.update_session_step(intake_session.id, current_step, completed=completed)
        if not updated:
            raise NotFoundError("IntakeSession", intake_session.id)
        intake_session = updated

    # Update analyses if provided
    if gap_analysis is not None:
        updated = JobService.save_gap_analysis(intake_session.id, gap_analysis)
        if updated:
            intake_session = updated

    if stakeholder_analysis is not None:
        updated = JobService.save_stakeholder_analysis(intake_session.id, stakeholder_analysis)
        if updated:
            intake_session = updated

    return {
        "id": intake_session.id,
        "job_id": intake_session.job_id,
        "current_step": intake_session.current_step,
        "step1_completed": intake_session.step1_completed,
        "step2_completed": intake_session.step2_completed,
        "step3_completed": intake_session.step3_completed,
        "gap_analysis": intake_session.gap_analysis,
        "stakeholder_analysis": intake_session.stakeholder_analysis,
        "created_at": intake_session.created_at.isoformat() if intake_session.created_at else None,
        "updated_at": intake_session.updated_at.isoformat() if intake_session.updated_at else None,
        "completed_at": intake_session.completed_at.isoformat() if intake_session.completed_at else None,
    }


@router.get("/jobs/{job_id}/intake-session/{session_id}/messages", response_model=list[dict])
async def get_intake_session_messages(
    job_id: int,
    session_id: int,
    step: int = Query(..., description="Step number (2 or 3)"),
    session: DBSession = None,  # noqa: ARG001
) -> list[dict]:
    """Get chat messages for an intake session step."""
    from api.services.chat_message_service import ChatMessageService
    
    # Verify the intake session exists and belongs to this job
    intake_session = JobService.get_intake_session(job_id)
    if not intake_session or intake_session.id != session_id:
        raise NotFoundError("IntakeSession", session_id)
    
    messages = ChatMessageService.get_messages_for_step(session_id, step)
    return messages


@router.post("/jobs/{job_id}/intake-session/{session_id}/messages", status_code=status.HTTP_204_NO_CONTENT)
async def save_intake_session_messages(
    job_id: int,
    session_id: int,
    step: int = Query(..., description="Step number (2 or 3)"),
    payload: dict = None,
    session: DBSession = None,  # noqa: ARG001
) -> None:
    """Save chat messages for an intake session step."""
    import json
    from api.services.chat_message_service import ChatMessageService
    
    # Verify the intake session exists and belongs to this job
    intake_session = JobService.get_intake_session(job_id)
    if not intake_session or intake_session.id != session_id:
        raise NotFoundError("IntakeSession", session_id)
    
    # Extract messages from payload
    messages = payload.get("messages", []) if payload else []
    messages_json = json.dumps(messages)
    
    # Save messages
    ChatMessageService.append_messages(session_id, step, messages_json)


@router.delete("/jobs/bulk-delete", response_model=BulkDeleteResponse)
async def bulk_delete_jobs(request: BulkDeleteRequest, session: DBSession = None) -> BulkDeleteResponse:  # noqa: ARG001
    """Delete multiple jobs in a single transaction."""
    successful, failed = JobService.delete_jobs(request.job_ids)
    return BulkDeleteResponse(successful=successful, failed=failed)

