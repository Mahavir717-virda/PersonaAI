"""WhatsApp platform connector implementation."""

from datetime import datetime, timezone
import uuid
from collections.abc import AsyncIterator
from typing import Any

from app.connectors.base import BaseConnector
from app.connectors.manifest import ConnectorManifest, ConnectorCapabilities
from app.connectors.registry import ConnectorRegistry
from app.models.communication import Communication, Participant, Attachment
from app.enums.platform import Platform
from app.enums.communication_status import CommunicationStatus
from app.providers.whatsapp.provider import WhatsAppProvider


class WhatsAppConnector(BaseConnector):
    """WhatsApp Business integration client wrapper."""

    _manifest = ConnectorManifest(
        id="whatsapp",
        name="WhatsApp Business",
        version="1.0.0",
        supports_oauth=False,
        supports_webhooks=True,
        supports_sync=True,
        icon="MessageCircle",
        capabilities=ConnectorCapabilities(
            supports_search=False,
            supports_labels=False,
            supports_attachments=True,
            supports_threads=False,
            supports_push=True,
            supports_streaming=True,
            supports_drafts=False,
        ),
    )

    def __init__(self) -> None:
        self.credentials: dict[str, Any] = {}
        self.connected = False
        self.provider = WhatsAppProvider()

    @classmethod
    def get_manifest(cls) -> ConnectorManifest:
        return cls._manifest

    async def connect(self, credentials: dict[str, Any]) -> None:
        self.credentials = credentials
        self.connected = True

    async def disconnect(self) -> None:
        self.credentials = {}
        self.connected = False

    async def authorize(self, auth_data: dict[str, Any]) -> dict[str, Any]:
        return {
            "phone_number_id": auth_data.get("phone_number_id", "mock_phone_id"),
            "token": auth_data.get("token", "mock_wa_token"),
        }

    async def refresh_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        return credentials

    async def health(self) -> bool:
        return await self.provider.verify_credentials(self.credentials)

    async def fetch_messages(self, cursor: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
        messages = []
        async for msg in self.provider.fetch_messages(self.credentials, cursor=cursor):
            messages.append(msg)
        return messages, None

    async def fetch_threads(self, cursor: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
        return [], None

    async def fetch_attachments(self, message_id: str) -> list[dict[str, Any]]:
        return []

    def sync(self, cursor: str | None = None) -> AsyncIterator[dict[str, Any]]:
        return self.provider.fetch_messages(self.credentials, cursor=cursor)

    async def normalize(self, raw_data: dict[str, Any]) -> Communication:
        dt = datetime.fromtimestamp(int(raw_data["timestamp"]), tz=timezone.utc)
        
        communication = Communication(
            id=uuid.uuid4(),
            platform=Platform.WHATSAPP,
            platform_message_id=raw_data["id"],
            subject=None,
            body=raw_data["text"],
            status=CommunicationStatus.NEW,
            importance="medium",
            created_at=dt,
            metadata_fields={},
        )

        sender = Participant(
            id=uuid.uuid4(),
            name=raw_data["sender_name"],
            address=raw_data["phone"],
            type="sender"
        )
        communication.participants.append(sender)

        receiver = Participant(
            id=uuid.uuid4(),
            address="15550100", # System receiving number
            type="recipient"
        )
        communication.participants.append(receiver)

        for att in raw_data.get("attachments", []):
            attachment = Attachment(
                id=uuid.uuid4(),
                name=att["name"],
                content_type=att["content_type"],
                size_bytes=att["size_bytes"]
            )
            communication.attachments.append(attachment)

        return communication


# Register the connector
ConnectorRegistry.register("WHATSAPP", WhatsAppConnector)
