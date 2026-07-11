"""Compatibility module for Gmail-facing application services.

This file intentionally does not implement behavior. It establishes the
boundary for future Gmail application services while preserving the
existing import surface for the legacy package layout.
"""

from __future__ import annotations


class GmailApplicationServiceRegistry:
    """Placeholder registry for Gmail application services."""

    def __init__(self) -> None:
        self._services: dict[str, object] = {}

    def register(self, name: str, service: object) -> None:
        self._services[name] = service

    def get(self, name: str) -> object:
        return self._services[name]
