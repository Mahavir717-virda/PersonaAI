import pytest
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.database.base import Base
from app.brain.models.brain_models import Task as DBTask
from app.brain.schemas.state import BrainState, BrainContext, UserProfileSnapshot, AIMessage, MessageRole, CommunicationIntelligence, TaskPriority
from app.brain.task.deadline import DeadlineResolver
from app.brain.task.dependency import TaskDependencyBuilder
from app.brain.task.repository import TaskRepository
from app.brain.task.extractor import TaskExtractor
from app.brain.task.engine import TaskEngine


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


def test_deadline_resolver() -> None:
    """Verify DeadlineResolver parses tomorrow and weekdays."""
    ref_time = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc) # Thursday
    
    tomorrow = DeadlineResolver.resolve_relative_deadline("tomorrow", ref_time)
    assert tomorrow is not None
    assert tomorrow.day == 3
    
    friday = DeadlineResolver.resolve_relative_deadline("Friday", ref_time)
    assert friday is not None
    assert friday.day == 3  # Next day is Friday


def test_dependency_builder() -> None:
    """Verify TaskDependencyBuilder links depends_on titles."""
    raw = [
        {"title": "Task A", "depends_on": []},
        {"title": "Task B", "depends_on": ["Task A"]}
    ]
    resolved = TaskDependencyBuilder.build_dependencies(raw)
    assert len(resolved) == 2
    assert "Task A" in resolved[1]["resolved_dependencies"]


@pytest.mark.asyncio
async def test_task_repository(async_db_session: AsyncSession) -> None:
    """Verify TaskRepository saves and lists tasks."""
    repo = TaskRepository(async_db_session)
    user_id = uuid4()
    
    task = await repo.create_task(
        user_id=user_id,
        title="Submit report",
        priority="high"
    )
    assert task.id is not None
    
    tasks = await repo.get_tasks_by_user(user_id)
    assert len(tasks) == 1
    assert tasks[0].title == "Submit report"


@pytest.mark.asyncio
async def test_task_engine_execution(async_db_session: AsyncSession, default_context: BrainContext) -> None:
    """Verify TaskEngine executes and populates state when contains_task is True."""
    import app.brain.task.engine as engine_mod
    original_factory = engine_mod.async_session_factory
    engine_mod.async_session_factory = lambda: async_db_session
    
    try:
        mock_extractor = TaskExtractor()
        mock_extractor.extract_tasks = AsyncMock(return_value=[
            {"title": "Prepare Q3 budget", "owner": "John", "priority": "high", "deadline": "Friday", "status": "pending", "depends_on": []}
        ])

        engine = TaskEngine(extractor=mock_extractor)
        state = BrainState(context=default_context)
        
        # Set contains_task = True
        comm_state = CommunicationIntelligence(contains_task=True)
        state = state.update(communication_intelligence=comm_state)
        
        message = AIMessage(role=MessageRole.USER, sender="user", recipient="ai", content="Please prepare budget.")
        state = state.update(conversation=state.conversation.model_copy(update={"incoming_message": message}))
        
        updated_state = await engine.execute(state)
        
        # Should extract and populate tasks list
        assert len(updated_state.tasks) == 1
        assert updated_state.tasks[0].title == "Prepare Q3 budget"
        assert updated_state.tasks[0].priority == TaskPriority.HIGH
        
    finally:
        engine_mod.async_session_factory = original_factory


@pytest.mark.asyncio
async def test_task_engine_skipping(async_db_session: AsyncSession, default_context: BrainContext) -> None:
    """Verify TaskEngine skips execution when contains_task is False."""
    engine = TaskEngine()
    state = BrainState(context=default_context)
    
    # contains_task defaults to False
    assert state.communication_intelligence.contains_task is False
    
    message = AIMessage(role=MessageRole.USER, sender="user", recipient="ai", content="Hello!")
    state = state.update(conversation=state.conversation.model_copy(update={"incoming_message": message}))
    
    updated_state = await engine.execute(state)
    
    # Tasks list should remain empty
    assert len(updated_state.tasks) == 0
