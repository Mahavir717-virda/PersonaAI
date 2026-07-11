import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database.base import Base
from app.brain.models.brain_models import Knowledge, KnowledgeRelation
from app.brain.schemas.state import BrainState, BrainContext, UserProfileSnapshot, AIMessage, MessageRole
from app.brain.knowledge.entity_linker import EntityLinker
from app.brain.knowledge.relationship_builder import RelationshipBuilder
from app.brain.knowledge.graph_builder import GraphBuilder
from app.brain.knowledge.validator import FactValidator
from app.brain.knowledge.confidence import KnowledgeConfidence
from app.brain.knowledge.versioning import KnowledgeVersioning
from app.brain.knowledge.repository import KnowledgeRepository
from app.brain.knowledge.retriever import KnowledgeRetriever
from app.brain.knowledge.extractor import KnowledgeExtractor
from app.brain.knowledge.engine import KnowledgeEngine


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


import pytest_asyncio

@pytest_asyncio.fixture
async def async_db_session() -> AsyncSession:
    """Fixture providing an async in-memory SQLite database session."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
        
    await engine.dispose()


def test_entity_linker() -> None:
    """Verify EntityLinker resolves entity variants to canonical names."""
    existing = ["John Smith", "Project Atlas", "Google LLC"]
    
    # Matching variant "John" should resolve to canonical "John Smith"
    assert EntityLinker.resolve_canonical_name("John", existing) == "John Smith"
    assert EntityLinker.resolve_canonical_name("John Smith", existing) == "John Smith"
    
    # Dissimilar names should remain unchanged
    assert EntityLinker.resolve_canonical_name("Alice", existing) == "Alice"


def test_relationship_builder() -> None:
    """Verify RelationshipBuilder нормализует relationship triples."""
    builder = RelationshipBuilder()
    raw = [
        {"subject": "John", "predicate": "works_on", "object": "Atlas", "properties": {"since": "2026"}}
    ]
    existing = ["John Smith", "Project Atlas"]
    
    triples = builder.build_triples(raw, existing)
    assert len(triples) == 1
    assert triples[0]["subject"] == "John Smith"
    assert triples[0]["object"] == "Project Atlas"
    assert triples[0]["predicate"] == "works_on"


@pytest.mark.asyncio
async def test_fact_validator() -> None:
    """Verify FactValidator resolution fallback returns supersede."""
    validator = FactValidator()
    res = await validator.resolve_conflict("Deadline is Friday", "Deadline is Monday")
    
    assert res["has_conflict"] is True
    assert res["resolution"] == "supersede_a_with_b"


@pytest.mark.asyncio
async def test_knowledge_repository(async_db_session: AsyncSession) -> None:
    """Verify KnowledgeRepository performs node/edge creation and active node lookup."""
    repo = KnowledgeRepository(async_db_session)
    user_id = uuid4()
    
    node_a = await repo.create_node(user_id, "John Smith", "Manager", "Person")
    node_b = await repo.create_node(user_id, "Project Atlas", "Software project", "Project")
    
    relation = await repo.create_relation(node_a.id, node_b.id, "works_on")
    
    assert node_a.id is not None
    assert node_b.id is not None
    assert relation.id is not None

    # Load active nodes
    active = await repo.get_active_nodes(user_id)
    assert len(active) == 2

    # Load relations
    relations = await repo.get_relations_for_node(node_a.id)
    assert len(relations) == 1
    assert relations[0][1].title == "Project Atlas"


@pytest.mark.asyncio
async def test_knowledge_retriever(async_db_session: AsyncSession) -> None:
    """Verify KnowledgeRetriever compiles subgraph context for relevant keywords in query."""
    repo = KnowledgeRepository(async_db_session)
    retriever = KnowledgeRetriever(repo)
    user_id = uuid4()
    
    node_a = await repo.create_node(user_id, "John Smith", "Manager", "Person")
    node_b = await repo.create_node(user_id, "Project Atlas", "Software project", "Project")
    await repo.create_relation(node_a.id, node_b.id, "works_on")
    
    # Retrieve context matching "Project Atlas"
    context = await retriever.retrieve_factual_context(user_id, "Tell me about Project Atlas")
    assert "Project Atlas" in context
    # Should pull the relationship as well
    assert "John Smith" in context
    assert "works_on" in context


@pytest.mark.asyncio
async def test_knowledge_engine_pipeline(async_db_session: AsyncSession, default_context: BrainContext) -> None:
    """Verify KnowledgeEngine executes full extraction and updates response context."""
    # Pre-populate database
    repo = KnowledgeRepository(async_db_session)
    user_id = default_context.user_profile.user_id
    await repo.create_node(user_id, "Project Atlas", "Software project", "Project")

    import app.brain.knowledge.engine as engine_mod
    original_factory = engine_mod.async_session_factory
    engine_mod.async_session_factory = lambda: async_db_session
    
    try:
        mock_extractor = KnowledgeExtractor()
        mock_extractor.extract_entities = AsyncMock(return_value=[
            {"name": "Project Atlas", "type": "Project", "properties": {"description": "Updated project description"}}
        ])
        mock_extractor.extract_relationships = AsyncMock(return_value=[])

        engine = KnowledgeEngine(extractor=mock_extractor)
        state = BrainState(context=default_context)
        message = AIMessage(role=MessageRole.USER, sender="user", recipient="ai", content="Query Project Atlas")
        state = state.update(conversation=state.conversation.model_copy(update={"incoming_message": message}))
        
        updated_state = await engine.execute(state)
        
        # Injected graph facts should be appended to response context
        assert "### Retrieved Graph Facts:" in updated_state.response.context
        
    finally:
        engine_mod.async_session_factory = original_factory
