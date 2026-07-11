"""Authentication and authorization dependency providers."""

import uuid
from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.repositories.user import UserRepository
from app.models.user import User
from app.enums.role import UserRole
from app.enums.account_status import AccountStatus
from app.auth.jwt import decode_token
from app.exceptions.authentication import AuthenticationError, AuthorizationError

security = HTTPBearer(auto_error=False)
DatabaseSession = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    session: DatabaseSession,
) -> User:
    """Extract and validate the bearer token to retrieve the authenticated User."""
    if not credentials:
        raise AuthenticationError("Authorization header is missing or invalid")

    token = credentials.credentials
    payload = decode_token(token)

    if payload.get("type") != "access":
        raise AuthenticationError("Invalid token type")

    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError as e:
        raise AuthenticationError("Invalid token subject format") from e

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if not user:
        raise AuthenticationError("Authenticated user record not found")

    return user


async def require_authenticated_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Enforce that the user is fully active."""
    if current_user.status != AccountStatus.ACTIVE:
        raise AuthorizationError(f"Account is inactive or blocked: {current_user.status}")
    return current_user


async def require_admin(
    current_user: Annotated[User, Depends(require_authenticated_user)],
) -> User:
    """Enforce that the user has administrator privileges."""
    if current_user.role != UserRole.ADMIN:
        raise AuthorizationError("Administrator permissions are required to perform this action")
    return current_user


# Annotated Dependency Aliases
CurrentUser = Annotated[User, Depends(require_authenticated_user)]
AdminUser = Annotated[User, Depends(require_admin)]
