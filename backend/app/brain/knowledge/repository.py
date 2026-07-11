"""Database repository for Knowledge Graph nodes and edges in PostgreSQL."""

from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.brain.models.brain_models import Knowledge, KnowledgeRelation
from app.brain.knowledge.versioning import KnowledgeVersioning


class KnowledgeRepository(BaseRepository[Knowledge]):
    """SQLAlchemy Repository for managing Knowledge nodes and relationship edges."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Knowledge)

    async def create_node(
        self,
        user_id: UUID,
        title: str,
        content: str,
        knowledge_type: str = "Concept",
        source: str | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Knowledge:
        """Creates a new Knowledge Graph node."""
        node = Knowledge(
            id=uuid4(),
            user_id=user_id,
            title=title,
            content=content,
            knowledge_type=knowledge_type,
            source=source,
            metadata_=metadata or {},
        )
        self.session.add(node)
        await self.session.commit()
        return node

    async def create_relation(
        self,
        source_id: UUID,
        target_id: UUID,
        relation_type: str,
        metadata: Dict[str, Any] | None = None,
    ) -> KnowledgeRelation:
        """Creates a new directed edge linking two Knowledge Graph nodes."""
        relation = KnowledgeRelation(
            id=uuid4(),
            source_knowledge_id=source_id,
            target_knowledge_id=target_id,
            relation_type=relation_type,
            metadata_=metadata or {},
        )
        self.session.add(relation)
        await self.session.commit()
        return relation

    async def get_node_by_title(self, user_id: UUID, title: str) -> Optional[Knowledge]:
        """Loads a node by title, filtering out superseded facts."""
        stmt = (
            select(Knowledge)
            .where(Knowledge.user_id == user_id)
            .where(Knowledge.title == title)
        )
        result = await self.session.execute(stmt)
        nodes = result.scalars().all()
        
        # Filter for active node (not superseded)
        for node in nodes:
            meta = node.metadata_ or {}
            if not meta.get("superseded", False):
                return node
        
        return nodes[0] if nodes else None

    async def get_active_nodes(self, user_id: UUID) -> List[Knowledge]:
        """Retrieves all active (non-superseded) knowledge nodes for a user."""
        stmt = select(Knowledge).where(Knowledge.user_id == user_id)
        result = await self.session.execute(stmt)
        nodes = result.scalars().all()
        return [n for n in nodes if not (n.metadata_ or {}).get("superseded", False)]

    async def get_relations_for_node(self, node_id: UUID) -> List[Tuple[KnowledgeRelation, Knowledge]]:
        """Loads both incoming and outgoing relations and neighboring nodes from/to a node."""
        # Outgoing
        stmt_out = (
            select(KnowledgeRelation, Knowledge)
            .join(Knowledge, Knowledge.id == KnowledgeRelation.target_knowledge_id)
            .where(KnowledgeRelation.source_knowledge_id == node_id)
        )
        res_out = await self.session.execute(stmt_out)
        out_list = list(res_out.all())

        # Incoming
        stmt_in = (
            select(KnowledgeRelation, Knowledge)
            .join(Knowledge, Knowledge.id == KnowledgeRelation.source_knowledge_id)
            .where(KnowledgeRelation.target_knowledge_id == node_id)
        )
        res_in = await self.session.execute(stmt_in)
        in_list = list(res_in.all())

        return out_list + in_list

    async def resolve_supersedence(self, old_node: Knowledge, new_node_id: UUID, reason: str | None = None) -> None:
        """Marks an old fact node as superseded by a newer verified record."""
        superseded_node = KnowledgeVersioning.supersede_fact(old_node, new_node_id, reason)
        self.session.add(superseded_node)
        await self.session.commit()
