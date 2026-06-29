"""HTTP exception types."""

from fastapi import status

from app.exceptions.base import ApplicationError


class NotFoundError(ApplicationError):
    """Raised when a requested resource cannot be found."""

    def __init__(self, message: str = "Resource not found") -> None:
        """Initialize a not found error."""
        super().__init__(
            message,
            error_code="not_found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ConflictError(ApplicationError):
    """Raised when a request conflicts with current resource state."""

    def __init__(self, message: str = "Resource conflict") -> None:
        """Initialize a conflict error."""
        super().__init__(
            message,
            error_code="conflict",
            status_code=status.HTTP_409_CONFLICT,
        )
