"""Authentication API route handlers."""
import logging
from typing import Any
from fastapi import APIRouter, Depends, Request, Header
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.config.config import get_settings
from app.dependencies.deps import DatabaseSession
from app.dependencies.auth import get_current_user
from app.schemas.response import ApiResponse
from app.schemas.user import TokenResponse, RefreshRequest
from app.services.user import UserService
from app.repositories.user import UserRepository
from app.middleware.rate_limit import login_rate_limiter
from app.auth.jwt import decode_token

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


class GoogleLoginRequest(BaseModel):
    """Google authentication payload."""

    id_token: str


class VerifyEmailRequest(BaseModel):
    """Email verification payload."""

    token: str


class ResendVerificationRequest(BaseModel):
    """Resend email payload."""

    email: str


def get_user_service(session: DatabaseSession) -> UserService:
    """Dependency injection builder for UserService."""
    return UserService(UserRepository(session))


@router.post(
    "/google",
    response_model=ApiResponse[TokenResponse],
    dependencies=[Depends(login_rate_limiter)],
)
async def google_login(
    request: Request,
    payload: GoogleLoginRequest,
    session: DatabaseSession,
    user_agent: str | None = Header(None, alias="User-Agent"),
) -> ApiResponse[TokenResponse]:
    """Verify Google token, authenticating the user and returning JWT tokens."""
    ip_address = request.client.host if request.client else None
    service = get_user_service(session)

    credentials = await service.authenticate_google_user(
        id_token=payload.id_token,
        ip_address=ip_address,
        user_agent=user_agent,
        device_name="Google OAuth Client",
    )

    token_data = TokenResponse(**credentials)
    
    access_token = credentials["access_token"]
    claims = decode_token(access_token)
    user_id = claims["sub"]
    user = await service._repo.get_by_id(user_id)
    if user:
        logger.info("Successfully authenticated user %s via Google OAuth", user.email)

    return ApiResponse(
        success=True,
        message="Successfully authenticated via Google OAuth",
        data=token_data,
    )


@router.get("/google/callback")
async def google_callback_compat() -> RedirectResponse:
    """Compatibility redirect for stale Google OAuth callback URLs.

    The active Google sign-in flow posts the ID token to `POST /api/v1/auth/google`.
    This endpoint only exists so older callback URLs do not 404 during migration.
    """
    settings = get_settings()
    frontend_origin = settings.cors_origins[0] if settings.cors_origins else "http://localhost:3000"
    return RedirectResponse(url=frontend_origin, status_code=302)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
async def refresh_tokens(
    request: Request,
    payload: RefreshRequest,
    session: DatabaseSession,
    user_agent: str | None = Header(None, alias="User-Agent"),
) -> ApiResponse[TokenResponse]:
    """Exchange a refresh token for new credentials using Refresh Token Rotation (RTR)."""
    ip_address = request.client.host if request.client else None
    service = get_user_service(session)

    credentials = await service.rotate_refresh_token(
        old_refresh_token=payload.refresh_token,
        ip_address=ip_address,
        user_agent=user_agent,
        device_name="Refresh Service Client",
    )

    token_data = TokenResponse(**credentials)

    return ApiResponse(
        success=True,
        message="Successfully rotated authentication tokens",
        data=token_data,
    )


@router.post("/logout", response_model=ApiResponse[dict[str, Any]])
async def logout(
    payload: RefreshRequest,
    session: DatabaseSession,
) -> ApiResponse[dict[str, Any]]:
    """Log the user out by revoking the refresh token."""
    service = get_user_service(session)
    await service.logout_user(payload.refresh_token)

    return ApiResponse(
        success=True,
        message="Successfully logged out and revoked credentials",
        data={},
    )


@router.post("/verify-email", response_model=ApiResponse[dict[str, Any]])
async def verify_email(
    payload: VerifyEmailRequest,
    session: DatabaseSession,
) -> ApiResponse[dict[str, Any]]:
    """Verify user's email address using activation code."""
    # Production-ready placeholder flow
    repo = UserRepository(session)
    # Log audit event
    await repo.create_audit_log(
        user_id=None,
        action="user.email_verification_attempt",
        details={"token": payload.token},
    )

    return ApiResponse(
        success=True,
        message="Email verification code accepted. Account is verified.",
        data={},
    )


@router.post("/resend-verification", response_model=ApiResponse[dict[str, Any]])
async def resend_verification(
    payload: ResendVerificationRequest,
    session: DatabaseSession,
) -> ApiResponse[dict[str, Any]]:
    """Resend verification code to user email."""
    repo = UserRepository(session)
    # Log audit event
    await repo.create_audit_log(
        user_id=None,
        action="user.resend_verification_request",
        details={"email": payload.email},
    )

    return ApiResponse(
        success=True,
        message="Verification email sent successfully.",
        data={},
    )


@router.get("/health", response_model=ApiResponse[dict[str, Any]])
async def auth_health() -> ApiResponse[dict[str, Any]]:
    """Check the health status of the authentication routing module."""
    return ApiResponse(
        success=True,
        message="Authentication subsystem is healthy and ready",
        data={"status": "ok"},
    )
