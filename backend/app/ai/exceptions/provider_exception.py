"""AI provider exceptions."""

from typing import Any
from app.ai.exceptions.ai_exception import AIError

class ProviderError(AIError):
    """Base error raised when a provider interaction fails."""
    pass

class ProviderAuthenticationError(ProviderError):
    """Raised when authentication with the provider fails (e.g. invalid API key)."""
    def __init__(self, message: str = "Provider authentication failed", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, error_code="AI_PROVIDER_AUTHENTICATION_ERROR", status_code=401, details=details)

class ProviderRateLimitError(ProviderError):
    """Raised when the provider rate limit is exceeded."""
    def __init__(self, message: str = "Provider rate limit exceeded", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, error_code="AI_PROVIDER_RATE_LIMIT_ERROR", status_code=429, details=details)

class ProviderTimeoutError(ProviderError):
    """Raised when request to provider times out."""
    def __init__(self, message: str = "Provider request timed out", details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, error_code="AI_PROVIDER_TIMEOUT_ERROR", status_code=504, details=details)

class ProviderAPIError(ProviderError):
    """Raised for general/unhandled provider API response errors."""
    def __init__(self, message: str, status_code: int = 502, details: dict[str, Any] | None = None) -> None:
        super().__init__(message=message, error_code="AI_PROVIDER_API_ERROR", status_code=status_code, details=details)
