"""Resume management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, status
from fastapi.responses import Response

from api.dependencies import DBSession
from api.schemas.resume import ResumeCreate, ResumePreviewRequest, ResumeResponse, ResumeVersionResponse
from api.services.job_service import JobService
from api.services.resume_service import ResumeService
from api.utils.errors import NotFoundError
from src.features.resume.types import ResumeData

router = APIRouter()


@router.get("/jobs/{job_id}/resumes", response_model=list[ResumeVersionResponse])
async def list_resume_versions(job_id: int, session: DBSession) -> list[ResumeVersionResponse]:
    """List all resume versions for a job."""
    versions = ResumeService.list_versions(job_id)
    return [ResumeVersionResponse.model_validate(v) for v in versions]


@router.get("/jobs/{job_id}/resumes/current", response_model=ResumeResponse | None)
async def get_current_resume(job_id: int, session: DBSession) -> ResumeResponse | None:
    """Get current resume for a job. Returns null if no canonical resume exists."""
    # Verify job exists first
    job = JobService.get_job(job_id)
    if not job:
        raise NotFoundError("Job", job_id)

    resume = ResumeService.get_canonical(job_id)
    if not resume:
        return None
    return ResumeResponse.model_validate(resume)


@router.get("/jobs/{job_id}/resumes/{version_id}", response_model=ResumeVersionResponse)
async def get_resume_version(job_id: int, version_id: int, session: DBSession) -> ResumeVersionResponse:
    """Get a specific resume version."""
    version = ResumeService.get_version(version_id)
    if not version or version.job_id != job_id:
        raise NotFoundError("ResumeVersion", version_id)
    return ResumeVersionResponse.model_validate(version)


@router.post("/jobs/{job_id}/resumes", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
async def create_resume_version(
    job_id: int,
    resume_data: ResumeCreate,
    session: DBSession = None,  # noqa: ARG001
) -> ResumeVersionResponse:
    """Create a new resume version."""
    resume_json_data = ResumeData.model_validate_json(resume_data.resume_json)
    version = ResumeService.create_version(
        job_id=job_id,
        resume_data=resume_json_data,
        template_name=resume_data.template_name,
        event_type=resume_data.event_type,
        parent_version_id=resume_data.parent_version_id,
    )
    return ResumeVersionResponse.model_validate(version)


@router.patch("/jobs/{job_id}/resumes/{version_id}/pin", response_model=ResumeResponse)
async def pin_resume_version(job_id: int, version_id: int, session: DBSession = None) -> ResumeResponse:  # noqa: ARG001
    """Pin a resume version as the current resume."""
    resume = ResumeService.pin_canonical(job_id, version_id)
    return ResumeResponse.model_validate(resume)


@router.delete("/jobs/{job_id}/resumes/unpin", status_code=status.HTTP_204_NO_CONTENT)
async def unpin_resume(job_id: int, session: DBSession = None) -> None:  # noqa: ARG001
    """Unpin the canonical resume for a job."""
    ResumeService.unpin_canonical(job_id)


@router.get("/jobs/{job_id}/resumes/{version_id}/pdf", response_class=Response)
async def download_resume_pdf(job_id: int, version_id: int, session: DBSession = None) -> Response:  # noqa: ARG001
    """Download resume PDF for a specific version."""
    version = ResumeService.get_version(version_id)
    if not version or version.job_id != job_id:
        raise NotFoundError("ResumeVersion", version_id)

    # Render PDF bytes
    resume_data = ResumeData.model_validate_json(version.resume_json)
    pdf_bytes = ResumeService.render_preview(job_id, resume_data, version.template_name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume_{job_id}_v{version.version_index}.pdf"'},
    )


@router.post("/jobs/{job_id}/resumes/preview", response_class=Response)
async def preview_resume_pdf_draft(
    job_id: int,
    request: ResumePreviewRequest,
    session: DBSession = None,  # noqa: ARG001
) -> Response:
    """Preview resume PDF from draft data (no version required)."""
    resume_data = ResumeData.model_validate(request.resume_data)
    pdf_bytes = ResumeService.render_preview(job_id, resume_data, request.template_name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="resume_preview.pdf"'},
    )


@router.post("/jobs/{job_id}/resumes/{version_id}/preview", response_class=Response)
async def preview_resume_pdf(
    job_id: int,
    version_id: int,
    resume_data: ResumeData | None = None,
    template_name: str | None = None,
    session: DBSession = None,  # noqa: ARG001
) -> Response:
    """Preview resume PDF (can override data/template)."""
    version = ResumeService.get_version(version_id)
    if not version or version.job_id != job_id:
        raise NotFoundError("ResumeVersion", version_id)

    # Use provided data or version data
    if resume_data is None:
        resume_data = ResumeData.model_validate_json(version.resume_json)
    if template_name is None:
        template_name = version.template_name

    pdf_bytes = ResumeService.render_preview(job_id, resume_data, template_name)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": 'inline; filename="resume_preview.pdf"'},
    )


@router.get("/jobs/{job_id}/resumes/compare", response_model=dict)
async def compare_resume_versions(
    job_id: int,
    version1_id: int = Query(..., description="First version ID"),
    version2_id: int = Query(..., description="Second version ID"),
    session: DBSession = None,  # noqa: ARG001
) -> dict:
    """Compare two resume versions."""
    version1 = ResumeService.get_version(version1_id)
    if not version1 or version1.job_id != job_id:
        raise NotFoundError("ResumeVersion", version1_id)

    version2 = ResumeService.get_version(version2_id)
    if not version2 or version2.job_id != job_id:
        raise NotFoundError("ResumeVersion", version2_id)

    # Simple comparison - return both versions
    # More sophisticated diff logic can be added later
    return {
        "version1": ResumeVersionResponse.model_validate(version1).model_dump(),
        "version2": ResumeVersionResponse.model_validate(version2).model_dump(),
        "diff": {
            "template_changed": version1.template_name != version2.template_name,
            "content_changed": version1.resume_json != version2.resume_json,
        },
    }

