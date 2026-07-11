"""AI module base exceptions."""

from typing import Any
from app.exceptions.base import ApplicationError

class AIError(ApplicationError):
    """Base exception for all AI/Model related issues."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "AI_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )
