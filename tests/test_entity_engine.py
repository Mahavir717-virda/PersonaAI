import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from app.brain.schemas.state import BrainState, BrainContext, UserProfileSnapshot, AIMessage, MessageRole, EntityType
from app.brain.entity.normalizer import EntityNormalizer
from app.brain.entity.extractor import EntityExtractor
from app.brain.entity.engine import EntityEngine


@pytest.fixture
def default_context() -> BrainContext:
    profile = UserProfileSnapshot(
        user_id=uuid4(),
        timezone="UTC",
        language="en",
        permissions=["read"],
    )
    return BrainContext(
        session_id=uuid4(),
        tenant_id="test-tenant",
        user_profile=profile,
    )


def test_entity_normalizer_alias_merging() -> None:
    """Verify EntityNormalizer merges variants and adds to aliases list."""
    existing = [
        {
            "value": "John Smith",
            "type": "Person",
            "canonical_name": "John Smith",
            "aliases": ["John Smith"],
            "occurrences": 1,
            "confidence": 0.9,
            "properties": {}
        }
    ]
    
    extracted = [
        {
            "value": "John",
            "type": "Person",
            "canonical_name": "John Smith",
            "confidence": 0.8,
            "properties": {}
        }
    ]
    
    normalized = EntityNormalizer.normalize_variants(extracted, existing)
    assert len(normalized) == 1
    assert normalized[0]["canonical_name"] == "John Smith"
    assert "John" in normalized[0]["aliases"]
    assert normalized[0]["occurrences"] == 2


@pytest.mark.asyncio
async def test_entity_extractor_fallback() -> None:
    """Verify EntityExtractor falls back to simple NER capitalized parsing on connection error."""
    extractor = EntityExtractor()
    entities = await extractor.extract_entities("Find Project Atlas please.")
    
    # Capitalized words: Find, Project, Atlas
    # Excludes first word of sentence: Project, Atlas
    assert any(ent["value"] == "Project" for ent in entities)
    assert any(ent["value"] == "Atlas" for ent in entities)


@pytest.mark.asyncio
async def test_entity_engine_pipeline(default_context: BrainContext) -> None:
    """Verify EntityEngine execute updates BrainState.entities list."""
    mock_extractor = EntityExtractor()
    mock_extractor.extract_entities = AsyncMock(return_value=[
        {
            "value": "Atlas",
            "type": "Project",
            "start_char": 5,
            "end_char": 10,
            "canonical_name": "Project Atlas",
            "confidence": 0.95
        }
    ])

    engine = EntityEngine(extractor=mock_extractor)
    state = BrainState(context=default_context)
    message = AIMessage(
        role=MessageRole.USER,
        sender="user",
        recipient="ai",
        content="Open Atlas project."
    )
    state = state.update(conversation=state.conversation.model_copy(update={"incoming_message": message}))
    
    updated_state = await engine.execute(state)
    
    assert len(updated_state.entities) == 1
    entity = updated_state.entities[0]
    assert entity.entity_type == EntityType.PROJECT
    assert entity.metadata["canonical_name"] == "Project Atlas"
    assert "Atlas" in entity.metadata["aliases"]
