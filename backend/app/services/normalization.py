"""Normalization service implementation."""

from typing import Any
from app.connectors.base import BaseConnector
from app.models.communication import Communication


class NormalizationService:
    """Service delegation layer for normalizing external raw data payloads."""

    @staticmethod
    async def normalize(connector: BaseConnector, raw_data: dict[str, Any]) -> Communication:
        """Translate raw data to canonical Communication model."""
        return await connector.normalize(raw_data)
