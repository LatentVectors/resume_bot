"""User management API routes."""

from __future__ import annotations

from fastapi import APIRouter, status

from api.dependencies import DBSession
from api.schemas.user import UserCreate, UserResponse, UserUpdate
from api.services.user_service import UserService
from api.utils.errors import NotFoundError

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
async def list_users(session: DBSession) -> list[UserResponse]:
    """List all users."""
    users = UserService.list_users()
    return [UserResponse.model_validate(user) for user in users]


@router.get("/users/current", response_model=UserResponse)
async def get_current_user() -> UserResponse:
    """Get current user (for single-user mode)."""
    user = UserService.get_current_user()
    if not user:
        raise NotFoundError("User", "current")
    return UserResponse.model_validate(user)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, session: DBSession) -> UserResponse:
    """Get a specific user."""
    user = UserService.get_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    return UserResponse.model_validate(user)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, session: DBSession) -> UserResponse:
    """Create a new user."""
    # For single-user mode, we need a user_id - get current user or create
    # Since we're in API mode, we'll need to handle this differently
    # For now, assume we need to get/create a user
    current_user = UserService.get_current_user()
    if current_user:
        # Update existing user
        updated_user = UserService.update_user(current_user.id, **user_data.model_dump())
        if not updated_user:
            raise NotFoundError("User", current_user.id)
        return UserResponse.model_validate(updated_user)
    else:
        # Create new user
        user_id = UserService.create_user(**user_data.model_dump())
        new_user = UserService.get_user(user_id)
        if not new_user:
            raise ValueError("Failed to create user")
        return UserResponse.model_validate(new_user)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate, session: DBSession) -> UserResponse:
    """Update a user."""
    updates = user_data.model_dump(exclude_unset=True)
    updated_user = UserService.update_user(user_id, **updates)
    if not updated_user:
        raise NotFoundError("User", user_id)
    return UserResponse.model_validate(updated_user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, session: DBSession) -> None:
    """Delete a user."""
    user = UserService.get_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    # Note: UserService doesn't have delete method, but we can add it if needed
    # For now, raise NotImplementedError
    raise NotImplementedError("User deletion not implemented")


@router.get("/users/current", response_model=UserResponse)
async def get_current_user() -> UserResponse:
    """Get current user (for single-user mode)."""
    user = UserService.get_current_user()
    if not user:
        raise NotFoundError("User", "current")
    return UserResponse.model_validate(user)

