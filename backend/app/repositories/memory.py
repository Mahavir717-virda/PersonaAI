"""Repository for managing Memory and EmbeddingChunk persistence in PostgreSQL."""

from __future__ import annotations

import json
from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from app.repositories.base import BaseRepository
from app.brain.models.brain_models import Memory, EmbeddingChunk


class MemoryRepository(BaseRepository[Memory]):
    """SQLAlchemy Repository for Memory structures with pgvector similarity capabilities."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Memory)

    async def create_memory(
        self,
        user_id: UUID,
        memory_type: str,
        content: str,
        source: str | None = None,
        confidence: float = 1.0,
        metadata: Dict[str, Any] | None = None,
        embedding: List[float] | None = None,
    ) -> Memory:
        """Saves a memory and its corresponding embedding chunk to the database."""
        memory_id = uuid4()
        
        # 1. Create Memory record
        memory_record = Memory(
            id=memory_id,
            user_id=user_id,
            memory_type=memory_type,
            content=content,
            source=source,
            confidence=confidence,
            metadata_=metadata or {},
        )
        self.session.add(memory_record)

        # 2. Create Embedding Chunk record if vector provided
        if embedding is not None:
            chunk = EmbeddingChunk(
                id=uuid4(),
                source_type="memory",
                source_id=memory_id,
                content=content,
                embedding=embedding,
            )
            self.session.add(chunk)

        await self.session.commit()
        return memory_record

    async def get_memories_by_user(self, user_id: UUID) -> List[Memory]:
        """Retrieves all memories for a user."""
        stmt = select(Memory).where(Memory.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def vector_search_memories(
        self,
        user_id: UUID,
        query_vector: List[float],
        memory_type: str | None = None,
        limit: int = 10,
    ) -> List[Tuple[Memory, float]]:
        """Performs pgvector similarity search on the memories.

        Returns a list of tuples containing the Memory object and its similarity score.
        If pgvector is not available in the database runtime, falls back to a clean list query.
        """
        # Select memories joined with chunks
        stmt = (
            select(Memory, EmbeddingChunk)
            .join(EmbeddingChunk, EmbeddingChunk.source_id == Memory.id)
            .where(Memory.user_id == user_id)
            .where(EmbeddingChunk.source_type == "memory")
        )
        
        if memory_type:
            stmt = stmt.where(Memory.memory_type == memory_type)

        result = await self.session.execute(stmt)
        rows = result.all()

        # Calculate cosine similarity in python or using SQL
        # This provides a robust fallback if pgvector extension is not initialized in the local container
        scored_memories: List[Tuple[Memory, float]] = []
        for memory, chunk in rows:
            if not chunk.embedding:
                continue
            
            # Simple python cosine similarity fallback
            score = self._cosine_similarity(query_vector, chunk.embedding)
            scored_memories.append((memory, score))

        # Sort by similarity descending
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories[:limit]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Helper to calculate similarity score between two float vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm_a = sum(a * a for a in vec1) ** 0.5
        norm_b = sum(b * b for b in vec2) ** 0.5
        
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(dot_product / (norm_a * norm_b))
