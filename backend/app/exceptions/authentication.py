"""Authentication and authorization exceptions."""

from fastapi import status

from app.exceptions.base import ApplicationError


class AuthenticationError(ApplicationError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        """Initialize an authentication error."""
        super().__init__(
            message,
            error_code="authentication_error",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(ApplicationError):
    """Raised when an authenticated user lacks permission."""

    def __init__(self, message: str = "Permission denied") -> None:
        """Initialize an authorization error."""
        super().__init__(
            message,
            error_code="authorization_error",
            status_code=status.HTTP_403_FORBIDDEN,
        )
