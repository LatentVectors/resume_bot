"""Workflow API routes for LLM operations."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from api.dependencies import DBSession
from api.schemas.workflow import (
    ExperienceExtractionRequest,
    ExperienceExtractionResponse,
    GapAnalysisRequest,
    GapAnalysisResponse,
    ResumeChatRequest,
    ResumeChatResponse,
    ResumeGenerationRequest,
    ResumeGenerationResponse,
    StakeholderAnalysisRequest,
    StakeholderAnalysisResponse,
)
from api.services.job_intake_service.workflows import (
    analyze_job_experience_fit,
    analyze_stakeholders,
    extract_experience_updates,
    run_resume_chat,
)
from api.services.job_service import JobService
from api.services.resume_service import ResumeService
from api.utils.errors import QuotaExceededError
from src.database import Experience, db_manager
from src.exceptions import OpenAIQuotaExceededError

router = APIRouter()


@router.post("/workflows/gap-analysis", response_model=GapAnalysisResponse)
async def gap_analysis(request: GapAnalysisRequest, session: DBSession = None) -> GapAnalysisResponse:  # noqa: ARG001
    """Run gap analysis workflow."""
    from fastapi import HTTPException, status

    # Fetch experiences
    experiences = [db_manager.get_experience(exp_id) for exp_id in request.experience_ids]
    experiences = [e for e in experiences if e is not None]

    if not experiences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No valid experiences found"
        )

    try:
        analysis = analyze_job_experience_fit(job_description=request.job_description, experiences=experiences)
        return GapAnalysisResponse(analysis=analysis)
    except OpenAIQuotaExceededError:
        raise QuotaExceededError()


@router.post("/workflows/stakeholder-analysis", response_model=StakeholderAnalysisResponse)
async def stakeholder_analysis(request: StakeholderAnalysisRequest, session: DBSession = None) -> StakeholderAnalysisResponse:  # noqa: ARG001
    """Run stakeholder analysis workflow."""
    # Fetch experiences
    experiences = [db_manager.get_experience(exp_id) for exp_id in request.experience_ids]
    experiences = [e for e in experiences if e is not None]

    if not experiences:
        raise ValueError("No valid experiences found")

    try:
        analysis = analyze_stakeholders(job_description=request.job_description, experiences=experiences)
        return StakeholderAnalysisResponse(analysis=analysis)
    except OpenAIQuotaExceededError:
        raise QuotaExceededError()


@router.post("/workflows/experience-extraction", response_model=ExperienceExtractionResponse)
async def experience_extraction(request: ExperienceExtractionRequest, session: DBSession = None) -> ExperienceExtractionResponse:  # noqa: ARG001
    """Extract experience updates from conversation."""
    # Fetch experiences
    experiences = [db_manager.get_experience(exp_id) for exp_id in request.experience_ids]
    experiences = [e for e in experiences if e is not None]

    if not experiences:
        raise ValueError("No valid experiences found")

    # Convert chat messages from dict format to LangChain messages
    from langchain_core.messages import AIMessage, HumanMessage

    chat_messages = []
    for msg_dict in request.chat_messages:
        role = msg_dict.get("role", "")
        content = msg_dict.get("content", "")
        if role == "user":
            chat_messages.append(HumanMessage(content=content))
        elif role == "assistant":
            chat_messages.append(AIMessage(content=content))
        # Skip other message types for extraction

    try:
        suggestions = extract_experience_updates(chat_messages=chat_messages, experiences=experiences)
        return ExperienceExtractionResponse(suggestions=suggestions)
    except OpenAIQuotaExceededError:
        raise QuotaExceededError()


@router.post("/workflows/resume-chat", response_model=ResumeChatResponse)
async def resume_chat(request: ResumeChatRequest, session: DBSession = None) -> ResumeChatResponse:  # noqa: ARG001
    """Run resume refinement chat workflow."""
    # Get job
    job = JobService.get_job(request.job_id)
    if not job:
        raise ValueError(f"Job {request.job_id} not found")

    # Get selected version if provided
    selected_version = None
    if request.selected_version_id:
        selected_version = ResumeService.get_version(request.selected_version_id)
        if not selected_version or selected_version.job_id != request.job_id:
            raise ValueError(f"Resume version {request.selected_version_id} not found for job {request.job_id}")

    # Convert messages from schema format to LangChain messages
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

    messages = []
    for msg in request.messages:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            ai_msg = AIMessage(content=msg.content)
            if msg.tool_calls:
                ai_msg.tool_calls = msg.tool_calls  # type: ignore[assignment]
            messages.append(ai_msg)
        elif msg.role == "tool":
            messages.append(ToolMessage(content=msg.content, tool_call_id=msg.tool_call_id or ""))

    try:
        ai_message, version_id = run_resume_chat(
            messages=messages,
            job=job,
            selected_version=selected_version,
            gap_analysis=request.gap_analysis,
            stakeholder_analysis=request.stakeholder_analysis,
            work_experience=request.work_experience,
        )

        # Convert AI message to dict format
        message_dict = {
            "role": "assistant",
            "content": ai_message.content,
        }
        if hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
            message_dict["tool_calls"] = ai_message.tool_calls

        return ResumeChatResponse(message=message_dict, version_id=version_id)
    except OpenAIQuotaExceededError:
        raise QuotaExceededError()


@router.post("/workflows/resume-generation", response_model=ResumeGenerationResponse)
async def resume_generation(
    request: ResumeGenerationRequest,
    user_id: int = Query(..., description="User ID"),
    session: DBSession = None,  # noqa: ARG001
) -> ResumeGenerationResponse:
    """Generate resume using LangGraph agent."""
    # Note: ResumeService.generate_resume_for_job uses user_id to fetch experiences from DB
    # The request.experiences are not used directly - the service fetches from DB
    # This endpoint signature may need adjustment based on actual implementation
    try:
        resume_data = ResumeService.generate_resume_for_job(
            user_id=user_id,
            job_id=0,  # Not used in generation, but required by service signature
            prompt=request.job_description,
            existing_draft=request.resume_draft,
        )
        return ResumeGenerationResponse(resume_data=resume_data)
    except OpenAIQuotaExceededError:
        raise QuotaExceededError()

