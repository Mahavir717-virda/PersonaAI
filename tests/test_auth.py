"""Unit and integration tests for authentication and user management."""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from app.auth.jwt import create_access_token, create_refresh_token, decode_token
from app.security.crypto import generate_random_token, hash_token
from app.security.password import hash_password, verify_password
from app.enums.role import UserRole
from app.enums.account_status import AccountStatus
from app.auth.oauth import GoogleOAuthService, NormalizedProfile
from app.config.config import get_settings

settings = get_settings()



def test_jwt_token_creation_and_decoding():
    """Verify that JWT access and refresh tokens can be successfully created and decoded."""
    user_id = uuid.uuid4()
    
    # Access Token
    access_token = create_access_token(user_id, {"role": "admin"})
    payload = decode_token(access_token)
    
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "admin"
    assert payload["type"] == "access"
    
    # Refresh Token
    refresh_token = create_refresh_token(user_id)
    payload_refresh = decode_token(refresh_token)
    
    assert payload_refresh["sub"] == str(user_id)
    assert payload_refresh["type"] == "refresh"
    assert "jti" in payload_refresh


def test_password_hashing():
    """Verify that password hashing and verification works correctly."""
    password = "SuperSecretPassword123"
    hashed = hash_password(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_crypto_helpers():
    """Verify random token generation and hashing."""
    token = generate_random_token()
    hashed = hash_token(token)
    
    assert len(token) > 0
    assert len(hashed) == 64 # SHA-256 hex digest is 64 characters


import asyncio

@patch("app.auth.oauth.httpx.AsyncClient")
def test_google_oauth_service_verification(mock_client_class):
    """Verify Google token verification calls the Google API and returns NormalizedProfile."""
    async def run_test():
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Configure mock response from Google tokeninfo endpoint
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: {
            "iss": "https://accounts.google.com",
            "aud": settings.google_client_id,
            "sub": "google12345",
            "email": "testuser@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/avatar.png",
        }
        mock_client.get.return_value = mock_response
        
        service = GoogleOAuthService()
        profile = await service.verify_token("dummy_token")
        
        assert profile.google_id == "google12345"
        assert profile.email == "testuser@gmail.com"
        assert profile.full_name == "Test User"
        assert profile.avatar_url == "https://example.com/avatar.png"

    asyncio.run(run_test())

