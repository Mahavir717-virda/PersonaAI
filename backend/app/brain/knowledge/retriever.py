"""Retrieves semantic sub-graphs and factual entities from Knowledge Repository."""

from __future__ import annotations

from uuid import UUID
from typing import Dict, List, Set, Tuple
from app.brain.models.brain_models import Knowledge, KnowledgeRelation
from app.brain.knowledge.repository import KnowledgeRepository


class KnowledgeRetriever:
    """Retrieves structured context blocks by scanning semantic node and relation networks."""

    def __init__(self, repository: KnowledgeRepository) -> None:
        self.repository = repository

    async def retrieve_factual_context(self, user_id: UUID, query_text: str) -> str:
        """Finds matching active nodes in the query text, loads their relation subgraphs, and compiles context."""
        active_nodes = await self.repository.get_active_nodes(user_id)
        if not active_nodes:
            return ""

        query_lower = query_text.lower()
        matched_nodes: List[Knowledge] = []

        # Find direct title overlaps in query (e.g. "Project Atlas" in "What is the deadline for Project Atlas?")
        for node in active_nodes:
            if node.title.lower() in query_lower:
                matched_nodes.append(node)

        if not matched_nodes:
            return ""

        facts: List[str] = []
        visited_nodes: Set[UUID] = set()

        for node in matched_nodes:
            if node.id in visited_nodes:
                continue
            visited_nodes.add(node.id)

            facts.append(f"Fact: '{node.title}' is a {node.knowledge_type} ({node.content}).")

            # Load 1-hop outgoing relationships
            relations = await self.repository.get_relations_for_node(node.id)
            for relation, target_node in relations:
                facts.append(
                    f"Relationship: '{node.title}' [{relation.relation_type}] -> '{target_node.title}'."
                )

        return "\n".join(facts)
