"""Application validation exceptions."""

from typing import Any

from fastapi import status

from app.exceptions.base import ApplicationError


class ApplicationValidationError(ApplicationError):
    """Raised when application-level validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        *,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an application validation error."""
        super().__init__(
            message,
            error_code="application_validation_error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details,
        )
