"""API client for message endpoints with typed responses."""

from app.api_client.client import api_client
from api.schemas.message import MessageCreate, MessageResponse
from src.database import MessageChannel


class MessagesAPI:
    """API client for message endpoints with typed responses."""

    @staticmethod
    async def list_messages(job_id: int) -> list[MessageResponse]:
        """List all messages for a job. Returns list of MessageResponse models."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}/messages",
            response_model=MessageResponse,
        )

    @staticmethod
    async def create_message(
        job_id: int,
        channel: MessageChannel,
        body: str,
    ) -> MessageResponse:
        """Create a new message. Returns MessageResponse model."""
        return await api_client.post(
            f"/api/v1/jobs/{job_id}/messages",
            json=MessageCreate(channel=channel, body=body).model_dump(),
            response_model=MessageResponse,
        )

    @staticmethod
    async def delete_message(job_id: int, message_id: int) -> None:
        """Delete a message."""
        await api_client.delete(f"/api/v1/jobs/{job_id}/messages/{message_id}")

