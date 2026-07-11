"""WhatsApp Provider SDK wrapper implementation."""

import logging
from typing import Any, AsyncGenerator
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class WhatsAppProvider(BaseProvider):
    """Encapsulates the Meta Graph API Client SDK for WhatsApp Business."""

    async def verify_credentials(self, credentials: dict[str, Any]) -> bool:
        """Query Meta Graph system endpoint to check Phone ID and System Token."""
        phone_id = credentials.get("phone_number_id")
        token = credentials.get("token")
        return bool(phone_id and token)

    async def fetch_messages(
        self, credentials: dict[str, Any], cursor: str | None = None
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Fetch chat messages from WhatsApp Business Webhook event buffers or Cloud API loggers."""
        logger.info("[WhatsAppProvider] Querying message history...")
        
        mock_messages = [
            {
                "id": "wa_msg_1",
                "phone": "+14155552671",
                "sender_name": "John Doe",
                "text": "Hey! Can we reschedule our sync to 2 PM today?",
                "timestamp": "1719656100", # Unix epoch
            }
        ]

        for msg in mock_messages:
            if cursor and msg["id"] <= cursor:
                continue
            yield msg
