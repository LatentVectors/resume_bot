"""Message management API routes."""

from __future__ import annotations

from fastapi import APIRouter, status
from sqlmodel import select

from api.dependencies import DBSession
from api.schemas.message import MessageCreate, MessageResponse
from api.services.job_service import JobService
from api.utils.errors import NotFoundError
from src.database import Message as DbMessage
from src.database import db_manager

router = APIRouter()


@router.get("/jobs/{job_id}/messages", response_model=list[MessageResponse])
async def list_messages(job_id: int, session: DBSession) -> list[MessageResponse]:
    """List all messages for a job."""
    with db_manager.get_session() as session_obj:
        stmt = select(DbMessage).where(DbMessage.job_id == job_id).order_by(DbMessage.created_at.desc())
        messages = list(session_obj.exec(stmt))
    return [MessageResponse.model_validate(msg) for msg in messages]


@router.post("/jobs/{job_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(job_id: int, message_data: MessageCreate, session: DBSession = None) -> MessageResponse:  # noqa: ARG001
    """Create a new message."""
    message = JobService.create_message(job_id, message_data.channel, message_data.body)
    return MessageResponse.model_validate(message)


@router.delete("/jobs/{job_id}/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(job_id: int, message_id: int, session: DBSession) -> None:
    """Delete a message."""
    with db_manager.get_session() as session_obj:
        message = session_obj.get(DbMessage, message_id)
        if not message or message.job_id != job_id:
            raise NotFoundError("Message", message_id)
        session_obj.delete(message)
        session_obj.commit()

