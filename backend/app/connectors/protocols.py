"""Typing protocol for platform connectors."""

from typing import Any, AsyncIterator, Protocol, runtime_checkable
from app.connectors.manifest import ConnectorManifest
from app.models.communication import Communication


@runtime_checkable
class ConnectorProtocol(Protocol):
    """Protocol for static type validation of any platform connector."""

    @classmethod
    def get_manifest(cls) -> ConnectorManifest:
        ...

    async def connect(self, credentials: dict[str, Any]) -> None:
        ...

    async def disconnect(self) -> None:
        ...

    async def authorize(self, auth_data: dict[str, Any]) -> dict[str, Any]:
        ...

    async def refresh_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        ...

    async def health(self) -> bool:
        ...

    async def fetch_messages(self, cursor: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
        ...

    async def fetch_threads(self, cursor: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
        ...

    async def fetch_attachments(self, message_id: str) -> list[dict[str, Any]]:
        ...

    def sync(self, cursor: str | None = None) -> AsyncIterator[dict[str, Any]]:
        ...

    async def normalize(self, raw_data: dict[str, Any]) -> Communication:
        ...

    @property
    def supports_streaming(self) -> bool:
        ...

    @property
    def supports_webhooks(self) -> bool:
        ...
