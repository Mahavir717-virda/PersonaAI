"""Custom exceptions for platform connectors."""


class ConnectorError(Exception):
    """Base exception for all connector-related failures."""

    pass


class ConnectionError(ConnectorError):
    """Raised when connecting to the external service fails."""

    pass


class AuthorizationError(ConnectorError):
    """Raised when authentication credentials or tokens are invalid/expired."""

    pass


class SyncError(ConnectorError):
    """Raised when fetching or parsing data during a sync pass fails."""

    pass
