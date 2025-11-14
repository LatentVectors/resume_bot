"""Certificate management API routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, status

from api.dependencies import DBSession
from api.schemas.certificate import CertificateCreate, CertificateResponse, CertificateUpdate
from api.services.certificate_service import CertificateService
from api.utils.errors import NotFoundError

router = APIRouter()


@router.get("/certificates", response_model=list[CertificateResponse])
async def list_certificates(user_id: int = Query(..., description="User ID"), session: DBSession = None) -> list[CertificateResponse]:  # noqa: ARG001
    """List all certificates for a user."""
    certificates = CertificateService.list_user_certifications(user_id)
    return [CertificateResponse.model_validate(cert) for cert in certificates]


@router.post("/certificates", response_model=CertificateResponse, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    certificate_data: CertificateCreate,
    user_id: int = Query(..., description="User ID"),
    session: DBSession = None,  # noqa: ARG001
) -> CertificateResponse:
    """Create a new certificate."""
    certificate_id = CertificateService.create_certification(user_id, **certificate_data.model_dump())
    certificate = CertificateService.get_certification(certificate_id)
    if not certificate:
        raise ValueError("Failed to create certificate")
    return CertificateResponse.model_validate(certificate)


@router.patch("/certificates/{certificate_id}", response_model=CertificateResponse)
async def update_certificate(certificate_id: int, certificate_data: CertificateUpdate, session: DBSession) -> CertificateResponse:
    """Update a certificate."""
    updates = certificate_data.model_dump(exclude_unset=True)
    certificate = CertificateService.update_certification(certificate_id, **updates)
    if not certificate:
        raise NotFoundError("Certificate", certificate_id)
    return CertificateResponse.model_validate(certificate)


@router.delete("/certificates/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(certificate_id: int, session: DBSession) -> None:
    """Delete a certificate."""
    deleted = CertificateService.delete_certification(certificate_id)
    if not deleted:
        raise NotFoundError("Certificate", certificate_id)

