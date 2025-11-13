"""Response management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, status
from sqlmodel import select

from api.dependencies import DBSession
from api.schemas.response import ResponseCreate, ResponseResponse, ResponseUpdate
from api.utils.errors import NotFoundError
from src.database import Response as DbResponse, ResponseSource, db_manager

router = APIRouter()


@router.get("/responses", response_model=list[ResponseResponse])
async def list_responses(
    sources: list[str] | None = Query(None, description="Filter by sources"),
    ignore: bool | None = Query(None, description="Filter by ignore flag"),
    session: DBSession = None,  # noqa: ARG001
) -> list[ResponseResponse]:
    """List all responses with optional filters."""
    responses = db_manager.list_responses(sources=sources, ignore=ignore)
    return [ResponseResponse.model_validate(r) for r in responses]


@router.get("/responses/{response_id}", response_model=ResponseResponse)
async def get_response(response_id: int, session: DBSession) -> ResponseResponse:
    """Get a specific response."""
    with db_manager.get_session() as session_obj:
        response = session_obj.get(DbResponse, response_id)
    if not response:
        raise NotFoundError("Response", response_id)
    return ResponseResponse.model_validate(response)


@router.post("/responses", response_model=ResponseResponse, status_code=status.HTTP_201_CREATED)
async def create_response(response_data: ResponseCreate, session: DBSession = None) -> ResponseResponse:  # noqa: ARG001
    """Create a new response."""
    response = DbResponse(
        job_id=response_data.job_id,
        prompt=response_data.prompt,
        response=response_data.response,
        source=response_data.source,
        ignore=response_data.ignore,
    )
    with db_manager.get_session() as session_obj:
        session_obj.add(response)
        session_obj.commit()
        session_obj.refresh(response)
    return ResponseResponse.model_validate(response)


@router.patch("/responses/{response_id}", response_model=ResponseResponse)
async def update_response(response_id: int, response_data: ResponseUpdate, session: DBSession) -> ResponseResponse:
    """Update a response."""
    with db_manager.get_session() as session_obj:
        response = session_obj.get(DbResponse, response_id)
        if not response:
            raise NotFoundError("Response", response_id)

        updates = response_data.model_dump(exclude_unset=True)
        for key, value in updates.items():
            setattr(response, key, value)

        session_obj.add(response)
        session_obj.commit()
        session_obj.refresh(response)
    return ResponseResponse.model_validate(response)


@router.delete("/responses/{response_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_response(response_id: int, session: DBSession) -> None:
    """Delete a response."""
    with db_manager.get_session() as session_obj:
        response = session_obj.get(DbResponse, response_id)
        if not response:
            raise NotFoundError("Response", response_id)
        session_obj.delete(response)
        session_obj.commit()

