"""User API schemas."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.enums.role import UserRole
from app.enums.account_status import AccountStatus


class UserCreate(BaseModel):
    """Payload for user creation."""

    email: str
    full_name: str
    google_id: str | None = None
    avatar_url: str | None = None


class UserProfileRead(BaseModel):
    """Schema for profile identity details."""

    model_config = ConfigDict(from_attributes=True)

    full_name: str
    avatar_url: str | None = None


class UserSettingsRead(BaseModel):
    """Schema for general preferences and AI preferences."""

    model_config = ConfigDict(from_attributes=True)

    theme: str
    language: str
    timezone: str
    notification_preferences: str
    digest_frequency: str

    preferred_summary_length: str
    preferred_language: str
    ai_personality: str
    digest_schedule: str
    memory_enabled: bool


class UserRead(BaseModel):
    """Schema for reading User details."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    status: AccountStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None
    profile: UserProfileRead | None = None
    settings: UserSettingsRead | None = None


class UserUpdate(BaseModel):
    """Payload for updating user profile and UI settings."""

    full_name: str | None = None
    avatar_url: str | None = None
    theme: str | None = None
    language: str | None = None
    timezone: str | None = None


class TokenResponse(BaseModel):
    """Payload for returned credentials."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Payload for requesting new access token via refresh token."""

    refresh_token: str


class JWTClaims(BaseModel):
    """Internal model for token decoding payloads."""

    iss: str
    sub: str
    iat: int
    exp: int
    type: str
    jti: str | None = None
