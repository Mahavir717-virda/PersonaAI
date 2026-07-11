"""Base webhook handler contract."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseWebhookHandler(ABC):
    """Abstract contract every platform webhook event receiver must implement."""

    @abstractmethod
    async def verify_signature(self, raw_body: bytes, headers: Dict[str, str], secret: str) -> bool:
        """Verify request signature matching provider credentials."""
        pass

    @abstractmethod
    async def handle_payload(self, payload: Dict[str, Any]) -> None:
        """Process verified incoming event logs from the webhook."""
        pass
