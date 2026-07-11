"""Implementation of the EntityEngine."""

from __future__ import annotations

from typing import List

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState, Entity
from app.brain.entity.extractor import EntityExtractor
from app.brain.entity.normalizer import EntityNormalizer


class EntityEngine(BrainEngine):
    """Entity Extraction Engine parsing, linking, and standardizing entity variants."""

    def __init__(self, extractor: EntityExtractor | None = None) -> None:
        self.extractor = extractor or EntityExtractor()

    @property
    def name(self) -> str:
        return "entity"

    async def execute(self, state: BrainState) -> BrainState:
        incoming = state.conversation.incoming_message
        if not incoming or not incoming.content:
            return state

        # 1. Run LLM entity extractor
        extracted = await self.extractor.extract_entities(
            text=incoming.content,
            model=state.model_routing.selected_model,
        )

        if not extracted:
            return state

        # 2. Get existing state entities and convert to raw dicts for normalizer matching
        existing_dicts = []
        for ent in state.entities:
            existing_dicts.append({
                "value": ent.value,
                "type": ent.entity_type.value,
                "canonical_name": ent.metadata.get("canonical_name", ent.value),
                "aliases": ent.metadata.get("aliases", []),
                "occurrences": ent.metadata.get("occurrences", 1),
                "confidence": ent.confidence,
                "properties": ent.metadata.get("properties", {})
            })

        # 3. Normalize variant mappings
        normalized_dicts = EntityNormalizer.normalize_variants(extracted, existing_dicts)

        # 4. Reconstruct Pydantic Entity models
        updated_entities: List[Entity] = []
        for entry in normalized_dicts:
            canonical = entry.get("canonical_name", entry.get("value", ""))
            
            # Map clean entity type
            from app.brain.schemas.state import EntityType
            try:
                ent_type = EntityType(entry.get("type", "concept").lower())
            except ValueError:
                ent_type = EntityType.CONCEPT

            updated_entities.append(Entity(
                entity_type=ent_type,
                value=entry.get("value", canonical),
                start_char=entry.get("start_char", 0),
                end_char=entry.get("end_char", 0),
                confidence=entry.get("confidence", 1.0),
                metadata={
                    "canonical_name": canonical,
                    "aliases": entry.get("aliases", []),
                    "occurrences": entry.get("occurrences", 1),
                    "properties": entry.get("properties", {})
                }
            ))

        return state.update(entities=updated_entities)

    async def validate(self, state: BrainState) -> bool:
        return True

    async def rollback(self, state: BrainState) -> BrainState:
        return state
