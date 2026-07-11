"""Compatibility helpers for transitioning Gmail implementation into the new slice."""

from __future__ import annotations

from typing import Any


class GmailCompatibilityAdapter:
    """Thin adapter that preserves a stable interface while the migration evolves."""

    def __init__(self, implementation: Any | None = None) -> None:
        self._implementation = implementation

    def bind(self, implementation: Any) -> None:
        self._implementation = implementation

    def resolve(self) -> Any:
        return self._implementation
