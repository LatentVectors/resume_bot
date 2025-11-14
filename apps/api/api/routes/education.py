"""Education management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from api.dependencies import DBSession
from api.schemas.education import EducationCreate, EducationResponse, EducationUpdate
from api.services.education_service import EducationService
from api.utils.errors import NotFoundError

router = APIRouter()


@router.get("/education", response_model=list[EducationResponse])
async def list_education(user_id: int = Query(..., description="User ID"), session: DBSession = None) -> list[EducationResponse]:  # noqa: ARG001
    """List all education entries for a user."""
    educations = EducationService.list_user_educations(user_id)
    return [EducationResponse.model_validate(edu) for edu in educations]


@router.post("/education", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
async def create_education(
    education_data: EducationCreate,
    user_id: int = Query(..., description="User ID"),
    session: DBSession = None,  # noqa: ARG001
) -> EducationResponse:
    """Create a new education entry."""
    education_id = EducationService.create_education(user_id, **education_data.model_dump())
    education = EducationService.get_education(education_id)
    if not education:
        raise ValueError("Failed to create education")
    return EducationResponse.model_validate(education)


@router.patch("/education/{education_id}", response_model=EducationResponse)
async def update_education(education_id: int, education_data: EducationUpdate, session: DBSession) -> EducationResponse:
    """Update an education entry."""
    updates = education_data.model_dump(exclude_unset=True)
    education = EducationService.update_education(education_id, **updates)
    if not education:
        raise NotFoundError("Education", education_id)
    return EducationResponse.model_validate(education)


@router.delete("/education/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(education_id: int, session: DBSession) -> None:
    """Delete an education entry."""
    deleted = EducationService.delete_education(education_id)
    if not deleted:
        raise NotFoundError("Education", education_id)

