"""Connector lifecycle enums."""

from enum import StrEnum


class ConnectorState(StrEnum):
    """Supported connector lifecycle states."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
