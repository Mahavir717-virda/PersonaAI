"""External service connector package."""

from app.connectors.base import BaseConnector
from app.connectors.manager import ConnectorManager
from app.connectors.registry import ConnectorRegistry
from app.connectors.factory import ConnectorFactory

# Global instance of the connector manager
connector_manager = ConnectorManager()

__all__ = [
    "BaseConnector",
    "ConnectorManager",
    "ConnectorRegistry",
    "ConnectorFactory",
    "connector_manager",
]
