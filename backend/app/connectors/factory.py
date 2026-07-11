"""Connector factory for dynamic connector instantiations."""

from app.connectors.base import BaseConnector
from app.connectors.registry import ConnectorRegistry


class ConnectorFactory:
    """Factory class to dynamically instantiate registered connectors by name."""

    @staticmethod
    def create(platform_name: str) -> BaseConnector:
        """Instantiate a connector instance for the specified platform."""
        connector_class = ConnectorRegistry.get(platform_name)
        if not connector_class:
            raise ValueError(f"No connector registered for platform: '{platform_name}'")
        return connector_class()
