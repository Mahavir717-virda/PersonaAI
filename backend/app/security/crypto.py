"""Cryptographic and token generation helper functions."""

import hashlib
import secrets


def generate_random_token(length: int = 32) -> str:
    """Generate a cryptographically secure random url-safe token."""
    return secrets.token_urlsafe(length)


def hash_token(token: str) -> str:
    """Hash a token using SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
