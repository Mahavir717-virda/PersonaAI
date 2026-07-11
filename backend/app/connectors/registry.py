"""Connector registry to track all available platform connectors."""

from typing import Dict, Type
from app.connectors.base import BaseConnector


class ConnectorRegistry:
    """Registry maintaining active bindings between platform names and connector classes."""

    _registry: Dict[str, Type[BaseConnector]] = {}

    @classmethod
    def register(cls, name: str, connector_class: Type[BaseConnector]) -> None:
        """Register a new platform connector class."""
        cls._registry[name.upper()] = connector_class

    @classmethod
    def get(cls, name: str) -> Type[BaseConnector] | None:
        """Retrieve a registered connector class by platform key."""
        return cls._registry.get(name.upper())

    @classmethod
    def list_connectors(cls) -> Dict[str, Type[BaseConnector]]:
        """Return a copy of all registered connector classes."""
        return cls._registry.copy()
