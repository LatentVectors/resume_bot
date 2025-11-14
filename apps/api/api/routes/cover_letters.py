"""Cover letter management API routes."""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import Response

from api.dependencies import DBSession
from api.schemas.cover_letter import (
    CoverLetterCreate,
    CoverLetterPreviewRequest,
    CoverLetterResponse,
    CoverLetterVersionResponse,
)
from api.services.cover_letter_service import CoverLetterService
from api.services.job_service import JobService
from api.utils.errors import NotFoundError
from src.features.cover_letter.types import CoverLetterData

router = APIRouter()


@router.get("/jobs/{job_id}/cover-letters", response_model=list[CoverLetterVersionResponse])
async def list_cover_letter_versions(job_id: int, session: DBSession) -> list[CoverLetterVersionResponse]:
    """List all cover letter versions for a job."""
    versions = CoverLetterService.list_versions(job_id)
    return [CoverLetterVersionResponse.model_validate(v) for v in versions]


@router.get("/jobs/{job_id}/cover-letters/current", response_model=CoverLetterResponse | None)
async def get_current_cover_letter(job_id: int, session: DBSession) -> CoverLetterResponse | None:
    """Get current cover letter for a job. Returns null if no canonical cover letter exists."""
    # Verify job exists first
    job = JobService.get_job(job_id)
    if not job:
        raise NotFoundError("Job", job_id)

    cover_letter = CoverLetterService.get_canonical(job_id)
    if not cover_letter:
        return None
    return CoverLetterResponse.model_validate(cover_letter)


@router.get("/jobs/{job_id}/cover-letters/{version_id}", response_model=CoverLetterVersionResponse)
async def get_cover_letter_version(job_id: int, version_id: int, session: DBSession) -> CoverLetterVersionResponse:
    """Get a specific cover letter version."""
    versions = CoverLetterService.list_versions(job_id)
    version = next((v for v in versions if v.id == version_id), None)
    if not version:
        raise NotFoundError("CoverLetterVersion", version_id)
    return CoverLetterVersionResponse.model_validate(version)


@router.post("/jobs/{job_id}/cover-letters", response_model=CoverLetterVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_cover_letter_version(
    job_id: int,
    cover_letter_data: CoverLetterCreate,
    session: DBSession = None,  # noqa: ARG001
) -> CoverLetterVersionResponse:
    """Create a new cover letter version."""
    cover_letter_json_data = CoverLetterData.model_validate_json(cover_letter_data.cover_letter_json)
    version = CoverLetterService.create_version(
        job_id=job_id,
        cover_data=cover_letter_json_data,
        template_name=cover_letter_data.template_name,
    )
    return CoverLetterVersionResponse.model_validate(version)


@router.patch("/jobs/{job_id}/cover-letters/{version_id}/pin", response_model=CoverLetterResponse)
async def pin_cover_letter_version(job_id: int, version_id: int, session: DBSession = None) -> CoverLetterResponse:  # noqa: ARG001
    """Pin a cover letter version as the current cover letter."""
    cover_letter = CoverLetterService.pin_canonical(job_id, version_id)
    return CoverLetterResponse.model_validate(cover_letter)


@router.post("/jobs/{job_id}/cover-letters/preview", response_class=Response)
async def preview_cover_letter_pdf_draft(
    job_id: int,
    request: CoverLetterPreviewRequest,
    session: DBSession = None,  # noqa: ARG001
) -> Response:
    """Preview cover letter PDF from draft data (no version required)."""
    cover_letter_data = CoverLetterData.model_validate(request.cover_letter_data)
    pdf_bytes = CoverLetterService.render_preview(job_id, cover_letter_data, request.template_name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="cover_letter_preview.pdf"'},
    )


@router.get("/jobs/{job_id}/cover-letters/{version_id}/pdf", response_class=Response)
async def download_cover_letter_pdf(job_id: int, version_id: int, session: DBSession = None) -> Response:  # noqa: ARG001
    """Download cover letter PDF for a specific version."""
    versions = CoverLetterService.list_versions(job_id)
    version = next((v for v in versions if v.id == version_id), None)
    if not version:
        raise NotFoundError("CoverLetterVersion", version_id)

    # Render PDF bytes
    cover_data = CoverLetterData.model_validate_json(version.cover_letter_json)
    pdf_bytes = CoverLetterService.render_preview(job_id, cover_data, version.template_name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="cover_letter_{job_id}_v{version.version_index}.pdf"'},
    )

