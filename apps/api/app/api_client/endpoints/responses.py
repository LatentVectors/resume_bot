"""API client for response endpoints with typed responses."""

from api.schemas.response import ResponseCreate, ResponseResponse, ResponseUpdate
from app.api_client.client import api_client
from src.database import ResponseSource


class ResponsesAPI:
    """API client for response endpoints with typed responses."""

    @staticmethod
    async def list_responses(
        sources: list[str] | None = None,
        ignore: bool | None = None,
    ) -> list[ResponseResponse]:
        """List all responses with optional filters. Returns list of ResponseResponse models."""
        params: dict[str, str | bool | list[str]] = {}
        if sources:
            # FastAPI handles list query params as multiple params with same name
            params["sources"] = sources
        if ignore is not None:
            params["ignore"] = ignore
        return await api_client.get(
            "/api/v1/responses",
            params=params if params else None,
            response_model=ResponseResponse,
        )

    @staticmethod
    async def get_response(response_id: int) -> ResponseResponse:
        """Get a specific response. Returns ResponseResponse model."""
        return await api_client.get(
            f"/api/v1/responses/{response_id}",
            response_model=ResponseResponse,
        )

    @staticmethod
    async def create_response(
        prompt: str,
        response: str,
        source: ResponseSource,
        job_id: int | None = None,
        ignore: bool = False,
    ) -> ResponseResponse:
        """Create a new response. Returns ResponseResponse model."""
        return await api_client.post(
            "/api/v1/responses",
            json=ResponseCreate(
                job_id=job_id,
                prompt=prompt,
                response=response,
                source=source,
                ignore=ignore,
            ).model_dump(),
            response_model=ResponseResponse,
        )

    @staticmethod
    async def update_response(
        response_id: int,
        prompt: str | None = None,
        response: str | None = None,
        ignore: bool | None = None,
        locked: bool | None = None,
    ) -> ResponseResponse:
        """Update a response. Returns ResponseResponse model."""
        update_data = ResponseUpdate(
            prompt=prompt,
            response=response,
            ignore=ignore,
            locked=locked,
        ).model_dump(exclude_unset=True)
        return await api_client.patch(
            f"/api/v1/responses/{response_id}",
            json=update_data,
            response_model=ResponseResponse,
        )

    @staticmethod
    async def delete_response(response_id: int) -> None:
        """Delete a response."""
        await api_client.delete(f"/api/v1/responses/{response_id}")

