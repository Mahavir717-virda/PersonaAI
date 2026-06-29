"""Database exception types."""

from fastapi import status

from app.exceptions.base import ApplicationError


class DatabaseError(ApplicationError):
    """Raised when persistence operations fail."""

    def __init__(self, message: str = "Database operation failed") -> None:
        """Initialize a database error."""
        super().__init__(
            message,
            error_code="database_error",
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
