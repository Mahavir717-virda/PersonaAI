"""OAuth service integrations."""

from abc import ABC, abstractmethod
import httpx

from app.config.config import get_settings
from app.exceptions.authentication import AuthenticationError

settings = get_settings()


class NormalizedProfile:
    """Standardized profile structure returned by OAuth providers."""

    def __init__(
        self,
        google_id: str,
        email: str,
        full_name: str,
        avatar_url: str | None = None,
    ) -> None:
        self.google_id = google_id
        self.email = email
        self.full_name = full_name
        self.avatar_url = avatar_url


class OAuthService(ABC):
    """Abstract base class for all OAuth providers."""

    @abstractmethod
    async def verify_token(self, token: str) -> NormalizedProfile:
        """Verify the OAuth token and return the normalized user profile."""
        pass


class GoogleOAuthService(OAuthService):
    """Google OAuth 2.0 implementation."""

    async def verify_token(self, token: str) -> NormalizedProfile:
        """Verify Google ID token via Google's tokeninfo API."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://oauth2.googleapis.com/tokeninfo",
                    params={"id_token": token},
                    timeout=5.0,
                )
            except Exception as e:
                raise AuthenticationError(f"Google token verification request failed: {str(e)}")

            if response.status_code != 200:
                raise AuthenticationError("Invalid Google OAuth token")

            data = response.json()

            # Validate issuer
            iss = data.get("iss", "")
            if iss not in ("accounts.google.com", "https://accounts.google.com"):
                raise AuthenticationError("Google token has invalid issuer claim")

            # Validate audience (aud) unless the local config is set to default placeholder
            aud = data.get("aud", "")
            if (
                settings.google_client_id != "placeholder_google_client_id"
                and aud != settings.google_client_id
            ):
                raise AuthenticationError("Google token has invalid audience client ID")

            google_id = data.get("sub")
            email = data.get("email")
            full_name = data.get("name") or f"{data.get('given_name', '')} {data.get('family_name', '')}".strip()
            avatar_url = data.get("picture")

            if not google_id or not email:
                raise AuthenticationError("Google token is missing required profile info")

            return NormalizedProfile(
                google_id=google_id,
                email=email,
                full_name=full_name or "Google User",
                avatar_url=avatar_url,
            )
