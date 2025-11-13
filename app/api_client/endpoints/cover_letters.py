"""API client for cover letter endpoints with typed responses."""

from app.api_client.client import api_client
from api.schemas.cover_letter import CoverLetterCreate, CoverLetterResponse, CoverLetterVersionResponse


class CoverLettersAPI:
    """API client for cover letter endpoints with typed responses."""

    @staticmethod
    async def list_versions(job_id: int) -> list[CoverLetterVersionResponse]:
        """List all cover letter versions for a job. Returns list of CoverLetterVersionResponse models."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}/cover-letters",
            response_model=CoverLetterVersionResponse,
        )

    @staticmethod
    async def get_current(job_id: int) -> CoverLetterResponse:
        """Get current cover letter for a job. Returns CoverLetterResponse model."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}/cover-letters/current",
            response_model=CoverLetterResponse,
        )

    @staticmethod
    async def get_version(job_id: int, version_id: int) -> CoverLetterVersionResponse:
        """Get a specific cover letter version. Returns CoverLetterVersionResponse model."""
        return await api_client.get(
            f"/api/v1/jobs/{job_id}/cover-letters/{version_id}",
            response_model=CoverLetterVersionResponse,
        )

    @staticmethod
    async def create_version(
        job_id: int,
        cover_letter_json: str,
        template_name: str = "cover_000.html",
    ) -> CoverLetterVersionResponse:
        """Create a new cover letter version. Returns CoverLetterVersionResponse model."""
        return await api_client.post(
            f"/api/v1/jobs/{job_id}/cover-letters",
            json=CoverLetterCreate(
                cover_letter_json=cover_letter_json,
                template_name=template_name,
            ).model_dump(),
            response_model=CoverLetterVersionResponse,
        )

    @staticmethod
    async def pin_version(job_id: int, version_id: int) -> CoverLetterResponse:
        """Pin a cover letter version as the current cover letter. Returns CoverLetterResponse model."""
        return await api_client.patch(
            f"/api/v1/jobs/{job_id}/cover-letters/{version_id}/pin",
            response_model=CoverLetterResponse,
        )

    @staticmethod
    async def preview_pdf_draft(
        job_id: int,
        cover_letter_data: "CoverLetterData",  # type: ignore[name-defined]
        template_name: str,
    ) -> bytes:
        """Preview cover letter PDF from draft data (no version required). Returns PDF bytes."""
        from src.features.cover_letter.types import CoverLetterData

        response = await api_client.post(
            f"/api/v1/jobs/{job_id}/cover-letters/preview",
            json={
                "cover_letter_data": cover_letter_data.model_dump(),
                "template_name": template_name,
            },
            response_model=None,  # PDF is bytes, not a Pydantic model
        )
        if isinstance(response, bytes):
            return response
        raise ValueError("Unexpected response format for PDF")

    @staticmethod
    async def download_pdf(job_id: int, version_id: int) -> bytes:
        """Download cover letter PDF for a specific version. Returns PDF bytes."""
        response = await api_client.get(
            f"/api/v1/jobs/{job_id}/cover-letters/{version_id}/pdf",
            response_model=None,  # PDF is bytes, not a Pydantic model
        )
        if isinstance(response, bytes):
            return response
        raise ValueError("Unexpected response format for PDF")

    @staticmethod
    async def list_templates() -> list[str]:
        """List available cover letter templates. Returns list of template names."""
        from app.api_client.endpoints.templates import TemplatesAPI

        response = await TemplatesAPI.list_cover_letter_templates()
        return [template.name for template in response.templates]

