"""Boundary interfaces for the brain subsystem.

These are intentionally minimal placeholders that define the expected
contract between the communication domain and the future AI engines.
"""

from __future__ import annotations

from typing import Protocol, Any


class CommunicationIngestor(Protocol):
    """Consumes normalized communication data for brain processing."""

    async def ingest(self, payload: Any) -> None: ...
