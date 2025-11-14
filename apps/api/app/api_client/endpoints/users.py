"""API client for user endpoints with typed responses."""

from app.api_client.client import api_client
from api.schemas.user import UserCreate, UserResponse, UserUpdate


class UsersAPI:
    """API client for user endpoints with typed responses."""

    @staticmethod
    async def list_users() -> list[UserResponse]:
        """List all users. Returns list of UserResponse models."""
        return await api_client.get("/api/v1/users", response_model=UserResponse)

    @staticmethod
    async def get_user(user_id: int) -> UserResponse:
        """Get a user. Returns UserResponse model."""
        return await api_client.get(f"/api/v1/users/{user_id}", response_model=UserResponse)

    @staticmethod
    async def create_user(
        first_name: str,
        last_name: str,
        phone_number: str | None = None,
        email: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
        linkedin_url: str | None = None,
        github_url: str | None = None,
        website_url: str | None = None,
    ) -> UserResponse:
        """Create a user. Returns UserResponse model."""
        return await api_client.post(
            "/api/v1/users",
            json=UserCreate(
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                email=email,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
                linkedin_url=linkedin_url,
                github_url=github_url,
                website_url=website_url,
            ).model_dump(),
            response_model=UserResponse,
        )

    @staticmethod
    async def update_user(
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        phone_number: str | None = None,
        email: str | None = None,
        address: str | None = None,
        city: str | None = None,
        state: str | None = None,
        zip_code: str | None = None,
        linkedin_url: str | None = None,
        github_url: str | None = None,
        website_url: str | None = None,
    ) -> UserResponse:
        """Update a user. Returns UserResponse model."""
        update_data = UserUpdate(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            email=email,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            linkedin_url=linkedin_url,
            github_url=github_url,
            website_url=website_url,
        ).model_dump(exclude_unset=True)
        return await api_client.patch(
            f"/api/v1/users/{user_id}",
            json=update_data,
            response_model=UserResponse,
        )

    @staticmethod
    async def delete_user(user_id: int) -> None:
        """Delete a user."""
        await api_client.delete(f"/api/v1/users/{user_id}")

    @staticmethod
    async def get_current_user() -> UserResponse:
        """Get current user (for single-user mode). Returns UserResponse model."""
        return await api_client.get("/api/v1/users/current", response_model=UserResponse)

