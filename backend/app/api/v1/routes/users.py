"""User management API route handlers."""

from fastapi import APIRouter, Depends

from app.dependencies.deps import DatabaseSession
from app.dependencies.auth import CurrentUser
from app.schemas.response import ApiResponse
from app.schemas.user import UserRead, UserUpdate
from app.services.user import UserService
from app.repositories.user import UserRepository

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(session: DatabaseSession) -> UserService:
    """Dependency injection builder for UserService."""
    return UserService(UserRepository(session))


@router.get("/me", response_model=ApiResponse[UserRead])
async def get_my_profile(
    current_user: CurrentUser,
) -> ApiResponse[UserRead]:
    """Retrieve details and configuration for the currently authenticated User."""
    user_data = UserRead.model_validate(current_user)

    return ApiResponse(
        success=True,
        message="Successfully retrieved user profile",
        data=user_data,
    )


@router.patch("/me", response_model=ApiResponse[UserRead])
async def update_my_profile(
    payload: UserUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> ApiResponse[UserRead]:
    """Update profile identity or application settings details."""
    service = get_user_service(session)

    updated_user = await service.update_profile(
        user_id=current_user.id,
        full_name=payload.full_name,
        avatar_url=payload.avatar_url,
        theme=payload.theme,
        language=payload.language,
        timezone=payload.timezone,
    )

    user_data = UserRead.model_validate(updated_user)

    return ApiResponse(
        success=True,
        message="Successfully updated user profile",
        data=user_data,
    )
