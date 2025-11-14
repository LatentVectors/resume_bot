"""API client for job endpoints with typed responses."""

from api.schemas.job import JobCreate, JobResponse, JobUpdate
from app.api_client.client import api_client
from src.database import JobStatus


class JobsAPI:
    """API client for job endpoints with typed responses."""

    @staticmethod
    async def list_jobs(
        user_id: int,
        status_filter: JobStatus | None = None,
        favorite_only: bool = False,
    ) -> list[JobResponse]:
        """List jobs. Returns list of JobResponse models."""
        params: dict[str, str | int | bool] = {"user_id": user_id, "favorite_only": favorite_only}
        if status_filter:
            params["status_filter"] = status_filter.value
        return await api_client.get("/api/v1/jobs", params=params, response_model=JobResponse)

    @staticmethod
    async def get_job(job_id: int) -> JobResponse:
        """Get a job. Returns JobResponse model."""
        return await api_client.get(f"/api/v1/jobs/{job_id}", response_model=JobResponse)

    @staticmethod
    async def create_job(
        user_id: int,
        title: str | None,
        company: str | None,
        description: str,
        favorite: bool = False,
        status: JobStatus | None = None,
    ) -> JobResponse:
        """Create a job. Returns JobResponse model."""
        params = {"user_id": user_id}
        return await api_client.post(
            "/api/v1/jobs",
            params=params,
            json=JobCreate(
                title=title,
                company=company,
                description=description,
                favorite=favorite,
                status=status,
            ).model_dump(),
            response_model=JobResponse,
        )

    @staticmethod
    async def update_job(
        job_id: int,
        title: str | None = None,
        company: str | None = None,
        description: str | None = None,
        favorite: bool | None = None,
        status: JobStatus | None = None,
    ) -> JobResponse:
        """Update a job. Returns JobResponse model."""
        update_data = JobUpdate(
            title=title,
            company=company,
            description=description,
            favorite=favorite,
            status=status,
        ).model_dump(exclude_unset=True)
        return await api_client.patch(
            f"/api/v1/jobs/{job_id}",
            json=update_data,
            response_model=JobResponse,
        )

    @staticmethod
    async def delete_job(job_id: int) -> None:
        """Delete a job."""
        await api_client.delete(f"/api/v1/jobs/{job_id}")

    @staticmethod
    async def toggle_favorite(job_id: int, favorite: bool) -> JobResponse:
        """Toggle favorite status for a job. Returns JobResponse model."""
        return await api_client.patch(
            f"/api/v1/jobs/{job_id}/favorite",
            params={"favorite": favorite},
            response_model=JobResponse,
        )

    @staticmethod
    async def update_status(job_id: int, status: JobStatus) -> JobResponse:
        """Update job status. Returns JobResponse model."""
        return await api_client.patch(
            f"/api/v1/jobs/{job_id}/status",
            params={"status": status.value},
            response_model=JobResponse,
        )

    @staticmethod
    async def mark_as_applied(job_id: int) -> JobResponse:
        """Mark a job as applied. Returns JobResponse model."""
        return await api_client.post(f"/api/v1/jobs/{job_id}/apply", response_model=JobResponse)

    @staticmethod
    async def get_intake_session(job_id: int) -> dict:
        """Get intake session for a job. Returns dict."""
        return await api_client.get(f"/api/v1/jobs/{job_id}/intake-session")

    @staticmethod
    async def create_intake_session(job_id: int) -> dict:
        """Create intake session for a job. Returns dict."""
        return await api_client.post(f"/api/v1/jobs/{job_id}/intake-session")

    @staticmethod
    async def update_intake_session(
        job_id: int,
        current_step: int | None = None,
        step_completed: int | None = None,
        gap_analysis: str | None = None,
        stakeholder_analysis: str | None = None,
    ) -> dict:
        """Update intake session for a job. Returns dict."""
        params: dict[str, int | str] = {}
        if current_step is not None:
            params["current_step"] = current_step
        if step_completed is not None:
            params["step_completed"] = step_completed
        if gap_analysis is not None:
            params["gap_analysis"] = gap_analysis
        if stakeholder_analysis is not None:
            params["stakeholder_analysis"] = stakeholder_analysis
        return await api_client.patch(f"/api/v1/jobs/{job_id}/intake-session", params=params)

