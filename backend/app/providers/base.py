"""Base provider interface definition."""

from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator


class BaseProvider(ABC):
    """Abstract class every platform API provider (Gmail, WhatsApp, etc.) must inherit from."""

    @abstractmethod
    async def verify_credentials(self, credentials: dict[str, Any]) -> bool:
        """Check credential validity by hitting provider ping endpoints."""
        pass

    @abstractmethod
    async def fetch_messages(
        self, credentials: dict[str, Any], cursor: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Generator yielding raw API communication records from the provider."""
        pass
