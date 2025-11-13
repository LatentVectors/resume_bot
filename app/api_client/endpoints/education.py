"""API client for education endpoints with typed responses."""

from app.api_client.client import api_client
from api.schemas.education import EducationCreate, EducationResponse, EducationUpdate


class EducationAPI:
    """API client for education endpoints with typed responses."""

    @staticmethod
    async def list_education(user_id: int) -> list[EducationResponse]:
        """List all education entries for a user. Returns list of EducationResponse models."""
        return await api_client.get(
            "/api/v1/education",
            params={"user_id": user_id},
            response_model=EducationResponse,
        )

    @staticmethod
    async def create_education(
        user_id: int,
        institution: str,
        degree: str,
        major: str,
        grad_date: str,
    ) -> EducationResponse:
        """Create a new education entry. Returns EducationResponse model."""
        return await api_client.post(
            "/api/v1/education",
            params={"user_id": user_id},
            json=EducationCreate(
                institution=institution,
                degree=degree,
                major=major,
                grad_date=grad_date,
            ).model_dump(),
            response_model=EducationResponse,
        )

    @staticmethod
    async def update_education(
        education_id: int,
        institution: str | None = None,
        degree: str | None = None,
        major: str | None = None,
        grad_date: str | None = None,
    ) -> EducationResponse:
        """Update an education entry. Returns EducationResponse model."""
        update_data = EducationUpdate(
            institution=institution,
            degree=degree,
            major=major,
            grad_date=grad_date,
        ).model_dump(exclude_unset=True)
        return await api_client.patch(
            f"/api/v1/education/{education_id}",
            json=update_data,
            response_model=EducationResponse,
        )

    @staticmethod
    async def delete_education(education_id: int) -> None:
        """Delete an education entry."""
        await api_client.delete(f"/api/v1/education/{education_id}")

