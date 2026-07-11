"""Connector state enums."""

from enum import StrEnum


class ConnectorState(StrEnum):
    """Lifecycle states for active platform connectors."""

    DISCONNECTED = "disconnected"
    AUTHORIZING = "authorizing"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
    EXPIRED = "expired"
    RECONNECT_REQUIRED = "reconnect_required"
