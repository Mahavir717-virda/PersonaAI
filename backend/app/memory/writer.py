"""Reflective Memory Writer with policy verification and deduplication support."""

from __future__ import annotations

from uuid import UUID
from typing import Optional

from app.repositories.memory import MemoryRepository
from app.embeddings.provider import OllamaEmbeddingProvider
from app.memory.policy import MemoryPolicy
from app.memory.reflector import MemoryReflector
from app.memory.deduplicator import MemoryDeduplicator


class MemoryWriter:
    """Reflective memory writer that decides if information should be saved to long-term memory."""

    def __init__(
        self,
        repository: MemoryRepository,
        embedding_provider: OllamaEmbeddingProvider,
        reflector: MemoryReflector | None = None,
        deduplicator: MemoryDeduplicator | None = None,
    ) -> None:
        self.repository = repository
        self.embedding_provider = embedding_provider
        self.reflector = reflector or MemoryReflector()
        self.deduplicator = deduplicator or MemoryDeduplicator(repository)

    async def reflect_and_write(
        self,
        user_id: UUID,
        input_text: str,
        response_text: str,
        model: str | None = None,
    ) -> bool:
        """Asks local LLM to decide if the interaction contains persistent information, then writes it."""
        # 1. Enforce privacy policy rules
        if not MemoryPolicy.should_store(input_text):
            return False

        # 2. Reflect on conversation details
        reflection = await self.reflector.reflect(input_text, response_text, model)
        if not reflection:
            return False

        content = reflection["content"]
        memory_type = reflection["memory_type"]
        importance = reflection["importance"]

        # Enforce privacy policy rules on extracted standalone memory statement as well
        if not MemoryPolicy.should_store(content):
            return False

        # 3. Generate query vector embedding
        embedding = await self.embedding_provider.get_embedding(content)

        # 4. Check for duplicate matches and merge
        duplicate = await self.deduplicator.find_duplicate_and_merge(
            user_id=user_id,
            content=content,
            embedding=embedding,
        )
        if duplicate is not None:
            # Memory was successfully merged and updated rather than recreated
            return True

        # 5. Save as a new memory record
        await self.repository.create_memory(
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            confidence=1.0,
            metadata={
                "importance": importance,
                "access_count": 0,
                "pinned": False,
                "lifecycle_stage": "created",
            },
            embedding=embedding,
        )
        return True
