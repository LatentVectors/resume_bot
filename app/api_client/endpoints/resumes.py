"""API client for resume endpoints with typed responses."""

from app.api_client.client import api_client
from api.schemas.resume import ResumeCreate, ResumeResponse, ResumeVersionResponse
from src.database import ResumeVersionEvent
from src.features.resume.types import ResumeData


class ResumesAPI:
    """API client for resume endpoints with typed responses."""

    @staticmethod
    async def list_versions(job_id: int) -> list[ResumeVersionResponse]:
        """List all resume versions for a job. Returns list of ResumeVersionResponse models."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}/resumes",
            response_model=ResumeVersionResponse,
        )

    @staticmethod
    async def get_current(job_id: int) -> ResumeResponse:
        """Get current resume for a job. Returns ResumeResponse model."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}/resumes/current",
            response_model=ResumeResponse,
        )

    @staticmethod
    async def get_version(job_id: int, version_id: int) -> ResumeVersionResponse:
        """Get a specific resume version. Returns ResumeVersionResponse model."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}/resumes/{version_id}",
            response_model=ResumeVersionResponse,
        )

    @staticmethod
    async def create_version(
        job_id: int,
        template_name: str,
        resume_json: str,
        event_type: ResumeVersionEvent = ResumeVersionEvent.generate,
        parent_version_id: int | None = None,
    ) -> ResumeVersionResponse:
        """Create a new resume version. Returns ResumeVersionResponse model."""
        return await api_client.post(
            f"/api/v1/jobs/{job_id}/resumes",
            json=ResumeCreate(
                template_name=template_name,
                resume_json=resume_json,
                event_type=event_type,
                parent_version_id=parent_version_id,
            ).model_dump(),
            response_model=ResumeVersionResponse,
        )

    @staticmethod
    async def pin_version(job_id: int, version_id: int) -> ResumeResponse:
        """Pin a resume version as the current resume. Returns ResumeResponse model."""
        return await api_client.patch(
            f"/api/v1/jobs/{job_id}/resumes/{version_id}/pin",
            response_model=ResumeResponse,
        )

    @staticmethod
    async def download_pdf(job_id: int, version_id: int) -> bytes:
        """Download resume PDF for a specific version. Returns PDF bytes."""
        response = await api_client.get(
            f"/api/v1/jobs/{job_id}/resumes/{version_id}/pdf",
            response_model=None,  # PDF is bytes, not a Pydantic model
        )
        if isinstance(response, bytes):
            return response
        raise ValueError("Unexpected response format for PDF")

    @staticmethod
    async def preview_pdf_draft(
        job_id: int,
        resume_data: ResumeData,
        template_name: str,
    ) -> bytes:
        """Preview resume PDF from draft data (no version required). Returns PDF bytes."""
        response = await api_client.post(
            f"/api/v1/jobs/{job_id}/resumes/preview",
            json={
                "resume_data": resume_data.model_dump(),
                "template_name": template_name,
            },
            response_model=None,  # PDF is bytes, not a Pydantic model
        )
        if isinstance(response, bytes):
            return response
        raise ValueError("Unexpected response format for PDF")

    @staticmethod
    async def preview_pdf(
        job_id: int,
        version_id: int,
        resume_data: ResumeData | None = None,
        template_name: str | None = None,
    ) -> bytes:
        """Preview resume PDF (can override data/template). Returns PDF bytes."""
        json_data: dict[str, str | dict] = {}
        if resume_data:
            # Serialize ResumeData to dict for JSON
            json_data["resume_data"] = resume_data.model_dump()
        if template_name:
            json_data["template_name"] = template_name

        response = await api_client.post(
            f"/api/v1/jobs/{job_id}/resumes/{version_id}/preview",
            json=json_data if json_data else {},
            response_model=None,  # PDF is bytes, not a Pydantic model
        )
        if isinstance(response, bytes):
            return response
        raise ValueError("Unexpected response format for PDF")

    @staticmethod
    async def compare_versions(
        job_id: int,
        version1_id: int,
        version2_id: int,
    ) -> dict:
        """Compare two resume versions. Returns comparison dict."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}/resumes/compare",
            params={"version1_id": version1_id, "version2_id": version2_id},
        )

