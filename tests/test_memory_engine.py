import pytest
import math
from datetime import datetime, timezone, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database.base import Base
from app.brain.models.brain_models import Memory, EmbeddingChunk
from app.brain.schemas.state import BrainState, BrainContext, UserProfileSnapshot, AIMessage, MessageRole, MemoryLifecycleStage
from app.repositories.memory import MemoryRepository
from app.embeddings.provider import OllamaEmbeddingProvider
from app.memory.scorer import MemoryScorer
from app.memory.compressor import MemoryCompressor
from app.memory.writer import MemoryWriter
from app.memory.policy import MemoryPolicy
from app.memory.reflector import MemoryReflector
from app.memory.deduplicator import MemoryDeduplicator
from app.memory.context_builder import MemoryContextBuilder
from app.brain.engines.memory.engine import MemoryEngine


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


@pytest.mark.asyncio
async def test_memory_repository(async_db_session: AsyncSession) -> None:
    """Verify MemoryRepository correctly saves and queries database memory structures."""
    repo = MemoryRepository(async_db_session)
    user_id = uuid4()
    
    memory = await repo.create_memory(
        user_id=user_id,
        memory_type="semantic",
        content="John is user's manager",
        embedding=[0.1] * 768,
    )
    
    assert memory.id is not None
    assert memory.content == "John is user's manager"

    user_memories = await repo.get_memories_by_user(user_id)
    assert len(user_memories) == 1
    assert user_memories[0].id == memory.id


def test_memory_scorer_decay_curves() -> None:
    """Verify customized decay rates for procedural vs working memories."""
    scorer = MemoryScorer()
    
    # Working memory decays extremely fast (days_since=1 should zero it out)
    working_memory = Memory(
        id=uuid4(),
        memory_type="working",
        content="temporary context",
        created_at=datetime.now(timezone.utc) - timedelta(days=1),
    )
    
    # Procedural memory decays extremely slowly
    procedural_memory = Memory(
        id=uuid4(),
        memory_type="procedural",
        content="Concise reply constraint",
        created_at=datetime.now(timezone.utc) - timedelta(days=10),
    )
    
    working_score = scorer.score_memory(working_memory, similarity=0.9)
    procedural_score = scorer.score_memory(procedural_memory, similarity=0.9)
    
    # Procedural score remains high; working score drops close to 0 due to fast decay
    assert procedural_score > working_score


def test_privacy_memory_policy() -> None:
    """Verify MemoryPolicy correctly filters out passwords, credit cards, and OTPs."""
    # Policies should block sensitive details
    assert MemoryPolicy.should_store("password = supersecretpassword") is False
    assert MemoryPolicy.should_store("4111 2222 3333 4444") is False
    assert MemoryPolicy.should_store("Your verification OTP code is 12345") is False
    
    # Policies should allow preferences and manager names
    assert MemoryPolicy.should_store("My manager is John Smith") is True
    assert MemoryPolicy.should_store("User prefers dark mode layout") is True


@pytest.mark.asyncio
async def test_memory_deduplication(async_db_session: AsyncSession) -> None:
    """Verify MemoryDeduplicator detects duplicate facts and evolves the lifecycle stage."""
    repo = MemoryRepository(async_db_session)
    dedup = MemoryDeduplicator(repo)
    user_id = uuid4()
    
    # Save first memory record
    memory = await repo.create_memory(
        user_id=user_id,
        memory_type="semantic",
        content="Manager is John",
        embedding=[0.1] * 768,
        metadata={"access_count": 0, "lifecycle_stage": MemoryLifecycleStage.CREATED.value},
    )
    
    # Perform deduplication check with identical embedding
    merged = await dedup.find_duplicate_and_merge(
        user_id=user_id,
        content="Manager is John",
        embedding=[0.1] * 768,
    )
    
    assert merged is not None
    assert merged.id == memory.id
    # Confidence and frequency should have increased
    assert merged.metadata_["access_count"] == 1
    assert merged.metadata_["lifecycle_stage"] == MemoryLifecycleStage.CANDIDATE.value


def test_memory_context_builder() -> None:
    """Verify context builder structures and slices memories correctly."""
    working = ["working-1", "working-2"]
    episodic = ["episodic-1"]
    semantic = ["semantic-1"]
    procedural = ["procedural-1"]
    
    context = MemoryContextBuilder.build_context(working, episodic, semantic, procedural, top_k=1)
    
    assert "Active Session Context (Working Memory):" in context
    # Sliced to top_k = 1
    assert "working-1" in context
    assert "working-2" not in context
    assert "Recent Events (Episodic Memory):" in context


@pytest.mark.asyncio
async def test_memory_writer_integration(async_db_session: AsyncSession) -> None:
    """Verify MemoryWriter uses reflector, policy, and deduplicator before database write."""
    repo = MemoryRepository(async_db_session)
    emb_provider = OllamaEmbeddingProvider()
    
    writer = MemoryWriter(repo, emb_provider)
    user_id = uuid4()
    
    # Trigger write-back
    committed = await writer.reflect_and_write(
        user_id=user_id,
        input_text="My manager is John",
        response_text="I will note down that John is your manager.",
    )
    assert committed is True
    
    # Verify policy blocks passwords from being written
    committed_sensitive = await writer.reflect_and_write(
        user_id=user_id,
        input_text="My password is supersecret",
        response_text="Noted.",
    )
    assert committed_sensitive is False


@pytest.mark.asyncio
async def test_advanced_memory_engine_retrieval(async_db_session: AsyncSession, default_context: BrainContext) -> None:
    """Verify advanced MemoryEngine successfully executes complete pipeline, producing reasons."""
    repo = MemoryRepository(async_db_session)
    user_id = default_context.user_profile.user_id
    
    await repo.create_memory(
        user_id=user_id,
        memory_type="semantic",
        content="Manager is John",
        embedding=[0.2] * 768,
        metadata={"lifecycle_stage": "created", "pinned": False},
    )
    
    # Mock global DB session factory
    import app.brain.engines.memory.engine as engine_mod
    original_factory = engine_mod.async_session_factory
    engine_mod.async_session_factory = lambda: async_db_session
    
    try:
        mock_emb = OllamaEmbeddingProvider()
        mock_emb.get_embedding = AsyncMock(return_value=[0.2] * 768)
        
        engine = MemoryEngine(embedding_provider=mock_emb)
        state = BrainState(context=default_context)
        message = AIMessage(role=MessageRole.USER, sender="user", recipient="ai", content="Who is my manager?")
        state = state.update(conversation=state.conversation.model_copy(update={"incoming_message": message}))
        
        updated_state = await engine.execute(state)
        
        # Verify advanced attributes are populated
        assert len(updated_state.memory.retrieved_memories) == 1
        assert "Manager is John" in updated_state.memory.retrieved_memories
        assert "Manager is John" in updated_state.memory.retrieval_reasons
        assert "Manager is John" in updated_state.memory.compiled_context
        assert updated_state.memory.lifecycle_stages["Manager is John"] == MemoryLifecycleStage.CREATED
        
    finally:
        engine_mod.async_session_factory = original_factory
