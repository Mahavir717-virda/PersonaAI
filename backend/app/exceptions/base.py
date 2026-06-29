"""Base application exceptions."""

from typing import Any


class ApplicationError(Exception):
    """Base exception for expected application failures."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str,
        status_code: int,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize an application error."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
