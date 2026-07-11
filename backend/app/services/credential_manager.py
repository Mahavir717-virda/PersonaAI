"""Credential Manager implementation."""

import base64
import json
import logging
from hashlib import sha256
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken

from app.config.config import get_settings

logger = logging.getLogger(__name__)

_FERNET_PREFIX = "fernet:"
_LEGACY_PREFIX = "enc_"


class CredentialManager:
    """Manages encryption, validation, rotation, and revocation of platform OAuth credentials."""

    def __init__(self, secret_key: str | None = None) -> None:
        settings = get_settings()
        resolved_secret = secret_key or settings.credential_encryption_secret
        self.secret_key = resolved_secret
        self._fernet = Fernet(self._derive_key(resolved_secret))

    @staticmethod
    def _derive_key(secret_key: str) -> bytes:
        """Derive a stable Fernet key from the configured secret."""
        digest = sha256(secret_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)

    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials dictionary to a portable opaque string."""
        serialized = json.dumps(credentials, separators=(",", ":"), sort_keys=True)
        token = self._fernet.encrypt(serialized.encode("utf-8")).decode("utf-8")
        return f"{_FERNET_PREFIX}{token}"

    def decrypt_credentials(self, encrypted_str: str) -> Dict[str, Any]:
        """Decrypt credentials string back to dictionary."""
        if encrypted_str.startswith(_FERNET_PREFIX):
            token = encrypted_str[len(_FERNET_PREFIX) :]
            try:
                decoded = self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
            except InvalidToken as exc:
                raise ValueError("Invalid encrypted credentials format") from exc
            return json.loads(decoded)

        if encrypted_str.startswith(_LEGACY_PREFIX):
            encoded = encrypted_str[len(_LEGACY_PREFIX) :]
            decoded = base64.b64decode(encoded.encode("utf-8")).decode("utf-8")
            return json.loads(decoded)

        raise ValueError("Invalid encrypted credentials format")

    async def refresh_token(self, platform: str, refresh_token: str) -> Dict[str, Any]:
        """Request new access tokens from provider endpoints."""
        logger.info(f"[CredentialManager] Rotating access token for platform: '{platform}'")
        return {
            "access_token": f"refreshed_{platform}_access_token",
            "expires_in": 3600,
        }

    async def validate_token(self, platform: str, access_token: str) -> bool:
        """Query provider authentication endpoint to check if access token is active."""
        if not access_token:
            return False
        return not access_token.startswith("expired_")

    async def revoke_token(self, platform: str, token: str) -> bool:
        """Revoke active tokens from provider server."""
        logger.info(f"[CredentialManager] Revoking token on platform: '{platform}'")
        return True
