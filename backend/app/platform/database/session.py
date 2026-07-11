"""Platform-level database session boundary.

This module is intentionally lightweight and acts as a placeholder for the
future database abstraction layer during the architecture migration.
"""

from __future__ import annotations

from typing import Any


class PlatformSessionFactory:
    """Placeholder factory for platform-scoped database sessions."""

    def __init__(self, session_factory: Any | None = None) -> None:
        self._session_factory = session_factory

    def bind(self, session_factory: Any) -> None:
        self._session_factory = session_factory

    def get_session_factory(self) -> Any | None:
        return self._session_factory
