"""API client for template endpoints with typed responses."""

from app.api_client.client import api_client
from api.schemas.template import TemplateDetail, TemplateListResponse


class TemplatesAPI:
    """API client for template endpoints with typed responses."""

    @staticmethod
    async def list_resume_templates() -> TemplateListResponse:
        """List all available resume templates. Returns TemplateListResponse model."""
        return await api_client.get(
            "/api/v1/templates/resumes",
            response_model=TemplateListResponse,
        )

    @staticmethod
    async def get_resume_template(template_id: str) -> TemplateDetail:
        """Get a specific resume template. Returns TemplateDetail model."""
        return await api_client.get(
            f"/api/v1/templates/resumes/{template_id}",
            response_model=TemplateDetail,
        )

    @staticmethod
    async def list_cover_letter_templates() -> TemplateListResponse:
        """List all available cover letter templates. Returns TemplateListResponse model."""
        return await api_client.get(
            "/api/v1/templates/cover-letters",
            response_model=TemplateListResponse,
        )

    @staticmethod
    async def get_cover_letter_template(template_id: str) -> TemplateDetail:
        """Get a specific cover letter template. Returns TemplateDetail model."""
        return await api_client.get(
            f"/api/v1/templates/cover-letters/{template_id}",
            response_model=TemplateDetail,
        )

