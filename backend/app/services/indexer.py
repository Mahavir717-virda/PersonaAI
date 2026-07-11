"""Search Indexer interface and adapters."""

from abc import ABC, abstractmethod
import logging
from app.models.communication import Communication

logger = logging.getLogger(__name__)


class Indexer(ABC):
    """Abstract contract for indexing communications for search retrieval."""

    @abstractmethod
    async def index(self, communication: Communication) -> None:
        """Push a normalized communication into the search index."""
        pass


class PostgresIndexer(Indexer):
    """Saves and updates standard relational columns for default text searches."""

    async def index(self, communication: Communication) -> None:
        """Postgres database indexes records on write automatically. Stub for custom triggers."""
        logger.info(f"[Indexer] Indexed communication ID: {communication.id} into Postgres Search Index.")
