"""API client for certificate endpoints with typed responses."""

from app.api_client.client import api_client
from api.schemas.certificate import CertificateCreate, CertificateResponse, CertificateUpdate


class CertificatesAPI:
    """API client for certificate endpoints with typed responses."""

    @staticmethod
    async def list_certificates(user_id: int) -> list[CertificateResponse]:
        """List all certificates for a user. Returns list of CertificateResponse models."""
        return await api_client.get(
            "/api/v1/certificates",
            params={"user_id": user_id},
            response_model=CertificateResponse,
        )

    @staticmethod
    async def create_certificate(
        user_id: int,
        title: str,
        date: str,
        institution: str | None = None,
    ) -> CertificateResponse:
        """Create a new certificate. Returns CertificateResponse model."""
        return await api_client.post(
            "/api/v1/certificates",
            params={"user_id": user_id},
            json=CertificateCreate(
                title=title,
                institution=institution,
                date=date,
            ).model_dump(),
            response_model=CertificateResponse,
        )

    @staticmethod
    async def update_certificate(
        certificate_id: int,
        title: str | None = None,
        institution: str | None = None,
        date: str | None = None,
    ) -> CertificateResponse:
        """Update a certificate. Returns CertificateResponse model."""
        update_data = CertificateUpdate(
            title=title,
            institution=institution,
            date=date,
        ).model_dump(exclude_unset=True)
        return await api_client.patch(
            f"/api/v1/certificates/{certificate_id}",
            json=update_data,
            response_model=CertificateResponse,
        )

    @staticmethod
    async def delete_certificate(certificate_id: int) -> None:
        """Delete a certificate."""
        await api_client.delete(f"/api/v1/certificates/{certificate_id}")

