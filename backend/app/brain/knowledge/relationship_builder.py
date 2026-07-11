"""Structures and formats subject-predicate-object relationships."""

from __future__ import annotations

from typing import Any, Dict, List
from app.brain.knowledge.entity_linker import EntityLinker


class RelationshipBuilder:
    """Standardizes extracted relationship triples, linking nodes to canonical entities."""

    def __init__(self, linker: EntityLinker | None = None) -> None:
        self.linker = linker or EntityLinker()

    def build_triples(
        self,
        raw_relationships: List[Dict[str, Any]],
        existing_entities: List[str]
    ) -> List[Dict[str, Any]]:
        """Cleans and resolves raw relationship dictionaries into normalized triples."""
        triples = []
        for rel in raw_relationships:
            raw_sub = rel.get("subject")
            raw_obj = rel.get("object")
            pred = rel.get("predicate")

            if not raw_sub or not raw_obj or not pred:
                continue

            # Link names to canonical representations
            sub = self.linker.resolve_canonical_name(raw_sub, existing_entities)
            obj = self.linker.resolve_canonical_name(raw_obj, existing_entities)

            triples.append({
                "subject": sub,
                "predicate": pred.strip().lower(),
                "object": obj,
                "properties": rel.get("properties") or {}
            })
        return triples
