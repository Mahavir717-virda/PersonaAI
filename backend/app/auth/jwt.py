"""JWT token generation and verification utility."""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt

from app.config.config import get_settings
from app.exceptions.authentication import AuthenticationError

settings = get_settings()


def create_access_token(subject: str | uuid.UUID, additional_claims: dict[str, Any] | None = None) -> str:
    """Create a short-lived JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    claims = {
        "iss": settings.app_name,
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    if additional_claims:
        claims.update(additional_claims)

    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str | uuid.UUID, additional_claims: dict[str, Any] | None = None) -> str:
    """Create a long-lived JWT refresh token."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.refresh_token_expire_days)

    claims = {
        "iss": settings.app_name,
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()), # Unique token identifier for token rotation tracking
    }
    if additional_claims:
        claims.update(additional_claims)

    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT. Raises AuthenticationError if invalid or expired."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.app_name,
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise AuthenticationError("Token signature has expired") from e
    except jwt.InvalidTokenError as e:
        raise AuthenticationError("Invalid authentication token") from e
