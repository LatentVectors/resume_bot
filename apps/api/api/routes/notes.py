"""Note management API routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from api.dependencies import DBSession
from api.schemas.note import NoteCreate, NoteResponse, NoteUpdate
from api.services.job_service import JobService
from api.utils.errors import NotFoundError

router = APIRouter()


@router.get("/jobs/{job_id}/notes", response_model=list[NoteResponse])
async def list_notes(job_id: int, session: DBSession = None) -> list[NoteResponse]:  # noqa: ARG001
    """List all notes for a job."""
    notes = JobService.list_notes(job_id)
    return [NoteResponse.model_validate(note) for note in notes]


@router.post("/jobs/{job_id}/notes", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    job_id: int,
    note_data: NoteCreate,
    session: DBSession = None,  # noqa: ARG001
) -> NoteResponse:
    """Create a new note for a job."""
    note = JobService.add_note(job_id, note_data.content)
    return NoteResponse.model_validate(note)


@router.patch("/jobs/{job_id}/notes/{note_id}", response_model=NoteResponse)
async def update_note(
    job_id: int,
    note_id: int,
    note_data: NoteUpdate,
    session: DBSession = None,  # noqa: ARG001
) -> NoteResponse:
    """Update a note."""
    note = JobService.update_note(note_id, note_data.content)
    if not note:
        raise NotFoundError("Note", note_id)
    return NoteResponse.model_validate(note)


@router.delete("/jobs/{job_id}/notes/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    job_id: int,
    note_id: int,
    session: DBSession = None,  # noqa: ARG001
) -> None:
    """Delete a note."""
    deleted = JobService.delete_note(note_id)
    if not deleted:
        raise NotFoundError("Note", note_id)

