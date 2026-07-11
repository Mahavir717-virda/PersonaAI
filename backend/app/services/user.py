"""User service orchestrating business flows for auth and user management."""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from app.services.base import BaseService
from app.repositories.user import UserRepository
from app.auth.oauth import GoogleOAuthService
from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.security.crypto import hash_token
from app.enums.account_status import AccountStatus
from app.exceptions.authentication import AuthenticationError, AuthorizationError


class UserService(BaseService):
    """Business service governing User accounts and identity workflows."""

    def __init__(
        self,
        user_repo: UserRepository,
        oauth_service: GoogleOAuthService | None = None,
    ) -> None:
        """Initialize the UserService with repositories and OAuth helper."""
        super().__init__()
        self._repo = user_repo
        self._oauth = oauth_service or GoogleOAuthService()

    async def authenticate_google_user(
        self,
        id_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
    ) -> dict[str, Any]:
        """Authenticate or register a user using a Google ID token.

        Implements automatic profile creation and session logging.
        """
        # Verify Google OAuth token
        profile = await self._oauth.verify_token(id_token)

        # Look up existing user
        user = await self._repo.get_by_google_id(profile.google_id)
        is_new_user = False

        if not user:
            # Fallback lookup by email to link existing local account
            user = await self._repo.get_by_email(profile.email)
            if user:
                # Link Google ID and update avatar
                user = await self._repo.update_user(
                    user,
                    google_id=profile.google_id,
                    avatar_url=profile.avatar_url,
                )
            else:
                # Register new user
                user = await self._repo.create_user(
                    email=profile.email,
                    full_name=profile.full_name,
                    google_id=profile.google_id,
                    avatar_url=profile.avatar_url,
                    is_verified=True, # OAuth verified emails are trusted
                )
                is_new_user = True

        # Check account status
        if user.status != AccountStatus.ACTIVE:
            # Record failed session attempt
            await self._repo.create_session(
                user_id=user.id,
                device=device_name,
                browser=user_agent,
                ip_address=ip_address,
                success=False,
                failure_reason=f"Account status is {user.status}",
            )
            raise AuthorizationError(f"Account is suspended or blocked: {user.status}")

        # Update last login timestamp
        await self._repo.update_last_login(user)

        # Generate JWT Credentials
        access_token = create_access_token(user.id, {"role": user.role})
        refresh_token_plain = create_refresh_token(user.id)
        refresh_hash = hash_token(refresh_token_plain)

        # Calculate refresh expiration (e.g. 7 days)
        refresh_claims = decode_token(refresh_token_plain)
        expires_at = datetime.fromtimestamp(refresh_claims["exp"], tz=timezone.utc)

        # Store RefreshToken in DB
        db_token = await self._repo.create_refresh_token(
            user_id=user.id,
            token_hash=refresh_hash,
            expires_at=expires_at,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Create active User Session record
        await self._repo.create_session(
            user_id=user.id,
            refresh_token_id=db_token.id,
            device=device_name,
            browser=user_agent,
            ip_address=ip_address,
            success=True,
        )

        # Log audit trail
        action = "user.register" if is_new_user else "user.login"
        await self._repo.create_audit_log(
            user_id=user.id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"provider": "google"},
        )

        await self._repo.session.commit()

        return {
            "access_token": access_token,
            "refresh_token": refresh_token_plain,
            "token_type": "bearer",
        }

    async def rotate_refresh_token(
        self,
        old_refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_name: str | None = None,
    ) -> dict[str, Any]:
        """Perform Refresh Token Rotation (RTR).

        If a revoked refresh token is reused, we revoke all sessions for breach protection.
        """
        try:
            claims = decode_token(old_refresh_token)
        except AuthenticationError as e:
            raise AuthenticationError("Invalid or expired refresh token") from e

        if claims.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = uuid.UUID(claims["sub"])
        token_hash = hash_token(old_refresh_token)

        # Fetch refresh token record
        db_token = await self._repo.get_refresh_token(token_hash)

        if not db_token:
            raise AuthenticationError("Refresh token not found or invalid")

        # RTR Breach Detection: if token is already revoked, revoke all tokens for this user
        if db_token.revoked_at is not None:
            await self._repo.revoke_all_user_tokens(user_id)
            await self._repo.create_audit_log(
                user_id=user_id,
                action="token.rtr_breach_detected",
                ip_address=ip_address,
                user_agent=user_agent,
                details={"revoked_token_id": str(db_token.id)},
            )
            raise AuthenticationError("Security alert: Token reuse detected. All sessions revoked.")

        # Revoke the used token
        await self._repo.revoke_refresh_token(db_token)

        # Verify user status
        user = await self._repo.get_by_id(user_id)
        if not user or user.status != AccountStatus.ACTIVE:
            raise AuthorizationError("User account is inactive or blocked")

        # Generate a new pair
        new_access_token = create_access_token(user.id, {"role": user.role})
        new_refresh_token_plain = create_refresh_token(user.id)
        new_refresh_hash = hash_token(new_refresh_token_plain)

        # Expiry timestamp
        new_claims = decode_token(new_refresh_token_plain)
        expires_at = datetime.fromtimestamp(new_claims["exp"], tz=timezone.utc)

        # Create new token record
        new_db_token = await self._repo.create_refresh_token(
            user_id=user.id,
            token_hash=new_refresh_hash,
            expires_at=expires_at,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Close old session and open new one
        await self._repo.create_session(
            user_id=user.id,
            refresh_token_id=new_db_token.id,
            device=device_name,
            browser=user_agent,
            ip_address=ip_address,
            success=True,
        )

        await self._repo.session.commit()

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token_plain,
            "token_type": "bearer",
        }

    async def logout_user(self, refresh_token: str) -> None:
        """Revoke a refresh token to perform user logout."""
        try:
            claims = decode_token(refresh_token)
            token_hash = hash_token(refresh_token)
            db_token = await self._repo.get_refresh_token(token_hash)
            if db_token:
                await self._repo.revoke_refresh_token(db_token)
                # Log logout action
                await self._repo.create_audit_log(
                    user_id=db_token.user_id,
                    action="user.logout",
                )
                await self._repo.session.commit()
        except Exception:
            # Silently handle to prevent leaking auth states
            pass

    async def update_profile(
        self,
        user_id: uuid.UUID,
        full_name: str | None = None,
        avatar_url: str | None = None,
        theme: str | None = None,
        language: str | None = None,
        timezone: str | None = None,
    ) -> Any:
        """Update profile information and custom UI settings."""
        user = await self._repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")

        # Update profile identity
        user = await self._repo.update_user(
            user=user,
            full_name=full_name,
            avatar_url=avatar_url,
        )

        # Update settings if supplied
        if theme is not None:
            user.settings.theme = theme
        if language is not None:
            user.settings.language = language
        if timezone is not None:
            user.settings.timezone = timezone

        self._repo.session.add(user.settings)
        await self._repo.session.flush()

        await self._repo.create_audit_log(
            user_id=user.id,
            action="user.profile_update",
            details={
                "updated_profile": full_name is not None or avatar_url is not None,
                "updated_settings": theme is not None or language is not None or timezone is not None,
            },
        )
        await self._repo.session.commit()
        return user
