"""Base file storage provider interface."""

from abc import ABC, abstractmethod


class StorageProvider(ABC):
    """Abstract contract every file storage backend must implement."""

    @abstractmethod
    async def save_file(self, filename: str, content: bytes) -> str:
        """Store binary data payload and return access URL/path."""
        pass

    @abstractmethod
    async def get_file(self, filename: str) -> bytes:
        """Fetch binary data from the storage engine."""
        pass

    @abstractmethod
    async def delete_file(self, filename: str) -> bool:
        """Remove file from storage."""
        pass
