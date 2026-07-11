"""User repository implementation."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.models.user import User, UserProfile, UserSettings
from app.models.refresh_token import RefreshToken
from app.models.session import UserSession
from app.models.audit_log import AuditLog


class UserRepository(BaseRepository[User]):
    """Repository handling all CRUD and query operations for Users and related relations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the UserRepository with the User model."""
        super().__init__(session, User)

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Retrieve a user by their UUID with profile and settings loaded."""
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.profile), selectinload(User.settings))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Retrieve a user by email address."""
        stmt = (
            select(User)
            .where(User.email == email)
            .options(selectinload(User.profile), selectinload(User.settings))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        """Retrieve a user by their Google OAuth ID."""
        stmt = (
            select(User)
            .where(User.google_id == google_id)
            .options(selectinload(User.profile), selectinload(User.settings))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        email: str,
        full_name: str,
        google_id: str | None = None,
        avatar_url: str | None = None,
        role: str = "user",
        is_verified: bool = False,
    ) -> User:
        """Create a new User, along with a default UserProfile and UserSettings."""
        user = User(
            email=email,
            google_id=google_id,
            role=role,
            is_verified=is_verified,
        )
        self.session.add(user)
        await self.session.flush()

        profile = UserProfile(
            user_id=user.id,
            full_name=full_name,
            avatar_url=avatar_url,
        )
        settings = UserSettings(
            user_id=user.id,
        )
        self.session.add(profile)
        self.session.add(settings)
        await self.session.flush()

        # Load relationships
        stmt = (
            select(User)
            .where(User.id == user.id)
            .options(selectinload(User.profile), selectinload(User.settings))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one()

    async def update_user(
        self,
        user: User,
        full_name: str | None = None,
        avatar_url: str | None = None,
        role: str | None = None,
        status: str | None = None,
        is_verified: bool | None = None,
    ) -> User:
        """Update user profile details and status info."""
        if role is not None:
            user.role = role
        if status is not None:
            user.status = status
        if is_verified is not None:
            user.is_verified = is_verified

        if full_name is not None:
            user.profile.full_name = full_name
        if avatar_url is not None:
            user.profile.avatar_url = avatar_url

        self.session.add(user)
        self.session.add(user.profile)
        await self.session.flush()
        return user

    async def update_last_login(self, user: User) -> User:
        """Update last login timestamp to the current UTC time."""
        user.last_login = datetime.now(timezone.utc)
        self.session.add(user)
        await self.session.flush()
        return user

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """Hard delete user record."""
        stmt = delete(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0

    # Refresh Token CRUD
    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RefreshToken:
        """Create a new RefreshToken record."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            device_name=device_name,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.session.add(token)
        await self.session.flush()
        return token

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        """Find a refresh token by its hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token: RefreshToken) -> None:
        """Revoke a specific refresh token."""
        token.revoked_at = datetime.now(timezone.utc)
        self.session.add(token)
        await self.session.flush()

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        """Revoke all active refresh tokens for a user (e.g. breach recovery/global logout)."""
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(revoked_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    # Session Tracking
    async def create_session(
        self,
        user_id: uuid.UUID,
        refresh_token_id: uuid.UUID | None = None,
        device: str | None = None,
        browser: str | None = None,
        ip_address: str | None = None,
        success: bool = True,
        failure_reason: str | None = None,
    ) -> UserSession:
        """Record a login attempt or session launch."""
        session = UserSession(
            user_id=user_id,
            refresh_token_id=refresh_token_id,
            device=device,
            browser=browser,
            ip_address=ip_address,
            success=success,
            failure_reason=failure_reason,
        )
        self.session.add(session)
        await self.session.flush()
        return session

    async def close_session(self, session_id: uuid.UUID) -> None:
        """Mark session as logged out."""
        stmt = (
            update(UserSession)
            .where(UserSession.id == session_id)
            .values(logout_at=datetime.now(timezone.utc))
        )
        await self.session.execute(stmt)

    # Audit Logging
    async def create_audit_log(
        self,
        user_id: uuid.UUID | None,
        action: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        """Log user and system level events for audit compliance."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        self.session.add(log)
        await self.session.flush()
        return log
