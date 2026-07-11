"""Universal base connector interface."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator
from app.connectors.manifest import ConnectorManifest
from app.models.communication import Communication


class BaseConnector(ABC):
    """Abstract class defining the contract for all platform connectors in PersonaAI."""

    @classmethod
    @abstractmethod
    def get_manifest(cls) -> ConnectorManifest:
        """Return the self-describing connector metadata and capabilities."""
        pass

    @abstractmethod
    async def connect(self, credentials: dict[str, Any]) -> None:
        """Open connections and configure active client instances using credentials."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connections and release external client resources."""
        pass

    @abstractmethod
    async def authorize(self, auth_data: dict[str, Any]) -> dict[str, Any]:
        """Perform OAuth handshake or validation, returning serialized credentials."""
        pass

    @abstractmethod
    async def refresh_credentials(self, credentials: dict[str, Any]) -> dict[str, Any]:
        """Refresh expired credentials (e.g. OAuth tokens)."""
        pass

    @abstractmethod
    async def health(self) -> bool:
        """Verify client connection health and credential validity."""
        pass

    @abstractmethod
    async def fetch_messages(self, cursor: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch raw message payloads with pagination cursor support."""
        pass

    @abstractmethod
    async def fetch_threads(self, cursor: str | None = None) -> tuple[list[dict[str, Any]], str | None]:
        """Fetch message conversations/threads with pagination cursor support."""
        pass

    @abstractmethod
    async def fetch_attachments(self, message_id: str) -> list[dict[str, Any]]:
        """Fetch raw metadata/contents of attachments for a specific message."""
        pass

    @abstractmethod
    def sync(self, cursor: str | None = None) -> AsyncIterator[dict[str, Any]]:
        """Run a synchronization pass, yielding raw message data for imports."""
        pass

    @abstractmethod
    async def normalize(self, raw_data: dict[str, Any]) -> Communication:
        """Normalize raw platform payload into a canonical DB Communication model."""
        pass

    @property
    def supports_streaming(self) -> bool:
        """Return if connector supports real-time socket connections."""
        return self.get_manifest().capabilities.supports_streaming

    @property
    def supports_webhooks(self) -> bool:
        """Return if connector supports webhook callbacks."""
        return self.get_manifest().supports_webhooks
