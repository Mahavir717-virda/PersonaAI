"""Memory Deduplication and Lifecycle evolution manager for PersonaAI."""

from __future__ import annotations

from typing import List, Tuple
from uuid import UUID
from datetime import datetime, timezone

from app.brain.models.brain_models import Memory
from app.repositories.memory import MemoryRepository
from app.brain.schemas.state import MemoryLifecycleStage


class MemoryDeduplicator:
    """Detects duplicate or matching facts, merges metadata, and updates memory lifecycle stages."""

    def __init__(self, repository: MemoryRepository, similarity_threshold: float = 0.85) -> None:
        self.repository = repository
        self.similarity_threshold = similarity_threshold

    async def find_duplicate_and_merge(
        self,
        user_id: UUID,
        content: str,
        embedding: List[float],
    ) -> Memory | None:
        """Checks the database for duplicate facts.

        If a match is found, merges access counts, boosts confidence, transitions
        the lifecycle stage, and returns the modified Memory record.
        """
        # Search the database for semantically similar memories
        matches = await self.repository.vector_search_memories(
            user_id=user_id,
            query_vector=embedding,
            limit=3,
        )

        for memory, similarity in matches:
            if similarity >= self.similarity_threshold:
                # Merge logic:
                meta = dict(memory.metadata_ or {})
                
                # 1. Update access frequency
                access_count = int(meta.get("access_count", 0)) + 1
                meta["access_count"] = access_count
                
                # 2. Increase confidence
                current_confidence = memory.confidence if memory.confidence is not None else 0.5
                # Confidence increments asymptotically towards 1.0 on repeats
                new_confidence = min(1.0, current_confidence + 0.1)
                memory.confidence = new_confidence

                # 3. Evolve Lifecycle Stage
                current_stage = meta.get("lifecycle_stage", MemoryLifecycleStage.CREATED.value)
                if current_stage == MemoryLifecycleStage.CREATED.value:
                    meta["lifecycle_stage"] = MemoryLifecycleStage.CANDIDATE.value
                elif current_stage == MemoryLifecycleStage.CANDIDATE.value and access_count >= 3:
                    meta["lifecycle_stage"] = MemoryLifecycleStage.VALIDATED.value
                elif current_stage == MemoryLifecycleStage.VALIDATED.value and access_count >= 10:
                    meta["lifecycle_stage"] = MemoryLifecycleStage.LONG_TERM.value

                memory.metadata_ = meta
                memory.updated_at = datetime.now(timezone.utc)
                
                # Commit updates to SQLAlchemy session
                self.repository.session.add(memory)
                await self.repository.session.commit()
                
                return memory

        return None
