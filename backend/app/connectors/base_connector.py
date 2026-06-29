"""Base connector contract for future communication integrations."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Generic, TypeVar

from app.core.communication import Communication
from app.enums.platform import Platform

RawItemT = TypeVar("RawItemT")


class BaseConnector(ABC, Generic[RawItemT]):
    """Abstract contract every future connector must implement."""

    platform: Platform

    @abstractmethod
    async def connect(self) -> None:
        """Open any resources required by the connector."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Release resources owned by the connector."""

    @abstractmethod
    async def fetch(self) -> AsyncIterator[RawItemT]:
        """Yield raw platform records from the connector."""

    @abstractmethod
    async def normalize(self, item: RawItemT) -> Communication:
        """Convert one raw platform record into a Communication object."""
