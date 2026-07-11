"""Connector lifecycle manager implementation."""

import logging
from typing import Any, Dict, List
from app.connectors.base import BaseConnector
from app.connectors.factory import ConnectorFactory
from app.connectors.registry import ConnectorRegistry

# Discover and register mock platforms on import
import app.connectors.gmail  # noqa: F401
import app.connectors.whatsapp  # noqa: F401

logger = logging.getLogger(__name__)


class ConnectorManager:
    """Manages active connector client instances, configuration lifecycles, and manifests."""

    def __init__(self) -> None:
        self._active_connectors: Dict[str, BaseConnector] = {}

    def get_available_manifests(self) -> List[dict]:
        """Return the manifests of all registered connectors in the system."""
        manifests = []
        for _, connector_class in ConnectorRegistry.list_connectors().items():
            manifests.append(connector_class.get_manifest().model_dump())
        return manifests

    async def get_connector(self, connector_id_str: str, platform_name: str, credentials: Dict[str, Any]) -> BaseConnector:
        """Retrieve or instantiate an active connector client."""
        key = f"{platform_name.lower()}_{connector_id_str}"
        if key in self._active_connectors:
            connector = self._active_connectors[key]
            if credentials:
                await connector.connect(credentials)
            return connector

        logger.info(f"Instantiating connector client for platform: '{platform_name}' (ID: {connector_id_str})")
        connector = ConnectorFactory.create(platform_name)
        await connector.connect(credentials)
        self._active_connectors[key] = connector
        return connector

    async def disconnect_connector(self, connector_id_str: str, platform_name: str) -> None:
        """Disconnect and remove an active connector client from memory."""
        key = f"{platform_name.lower()}_{connector_id_str}"
        if key in self._active_connectors:
            logger.info(f"Disconnecting connector client for platform: '{platform_name}' (ID: {connector_id_str})")
            connector = self._active_connectors[key]
            await connector.disconnect()
            del self._active_connectors[key]
