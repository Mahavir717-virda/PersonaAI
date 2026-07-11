import pytest
from uuid import uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database.base import Base

from app.brain.planning.models import Plan, Step
from app.brain.planning.dependency_builder import DependencyBuilder
from app.brain.planning.parallelizer import PlanParallelizer
from app.brain.planning.cost_estimator import CostEstimator
from app.brain.planning.duration_estimator import DurationEstimator
from app.brain.planning.fallback import PlanFallbackGenerator
from app.brain.planning.rollback import PlanRollbackGenerator
from app.brain.planning.validator import PlanValidator
from app.brain.planning.workflow import PlanWorkflow
from app.brain.planning.repository import PlanRepository
from app.brain.planning.planner import GoalPlanner
from app.brain.planning.engine import PlanningEngine
from app.brain.schemas.state import BrainState, BrainContext, UserProfileSnapshot, AIMessage, MessageRole


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
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
    await engine.dispose()


# Parametrized Goals (20 tests)
GOALS_LIST = [
    ("Reply to John's email", "gmail"),
    ("Schedule meeting next Monday", "calendar"),
    ("Prepare Q3 slide deck and review", None),
    ("Find free slot in Sarah's calendar", "calendar"),
    ("Send invitation for tomorrow", "calendar"),
    ("Submit code repository changes", None),
    ("Process outstanding invoices", None),
    ("Draft manager summary report", None),
    ("Archive completed workspace logs", None),
    ("Sync files to shared drive", None),
    ("Generate email responses to new thread", "gmail"),
    ("Update contact information details", None),
    ("Setup team calendar workspace", "calendar"),
    ("Review pending document modifications", None),
    ("Create reminder checkpoint task list", None),
    ("Query database performance log records", None),
    ("Send status report updates", "gmail"),
    ("Verify user permissions levels", None),
    ("Import contact list elements", None),
    ("Export workflow planning diagrams", None),
]

@pytest.mark.parametrize("goal_text, expected_tool", GOALS_LIST)
@pytest.mark.asyncio
async def test_planner_heuristic_generation(goal_text: str, expected_tool: Optional[str]) -> None:
    planner = GoalPlanner()
    plan = await planner.generate_plan(goal_text)
    assert plan.goal == goal_text
    assert len(plan.steps) >= 2
    if expected_tool:
        assert any(step.tool_required == expected_tool for step in plan.steps)


# Validation Topologies (10 tests)
TOPOLOGY_SCENARIOS = [
    # 1. Empty steps
    ([], False),
    # 2. Single step
    ([Step(step_id="1", title="A", description="d", order=1)], True),
    # 3. Simple sequence
    ([Step(step_id="1", title="A", description="d", order=1), Step(step_id="2", title="B", description="d", order=2, dependencies=["1"])], True),
    # 4. Simple cycle
    ([Step(step_id="1", title="A", description="d", order=1, dependencies=["2"]), Step(step_id="2", title="B", description="d", order=2, dependencies=["1"])], False),
    # 5. Missing dependency
    ([Step(step_id="1", title="A", description="d", order=1, dependencies=["999"])], False),
    # 6. Branching sequence
    ([Step(step_id="1", title="A", description="d", order=1), Step(step_id="2", title="B", description="d", order=2, dependencies=["1"]), Step(step_id="3", title="C", description="d", order=3, dependencies=["1"])], True),
    # 7. Self cycle
    ([Step(step_id="1", title="A", description="d", order=1, dependencies=["1"])], False),
    # 8. Loop with multi-dependency
    ([Step(step_id="1", title="A", description="d", order=1, dependencies=["3"]), Step(step_id="2", title="B", description="d", order=2, dependencies=["1"]), Step(step_id="3", title="C", description="d", order=3, dependencies=["2"])], False),
    # 9. Two separate nodes
    ([Step(step_id="1", title="A", description="d", order=1), Step(step_id="2", title="B", description="d", order=2)], True),
    # 10. Complex DAG sequence
    ([
        Step(step_id="1", title="A", description="d", order=1),
        Step(step_id="2", title="B", description="d", order=2, dependencies=["1"]),
        Step(step_id="3", title="C", description="d", order=3, dependencies=["1"]),
        Step(step_id="4", title="D", description="d", order=4, dependencies=["2", "3"])
    ], True),
]

@pytest.mark.parametrize("steps, expected_valid", TOPOLOGY_SCENARIOS)
def test_plan_validator_topologies(steps: List[Step], expected_valid: bool) -> None:
    plan = Plan(goal="Test validation", summary="test", steps=steps)
    assert PlanValidator.validate_plan(plan) == expected_valid


# Duration Estimation Scenarios (5 tests)
DURATION_SCENARIOS = [
    # 1. No parallel steps (sum)
    ([Step(step_id="1", title="A", description="d", order=1, estimated_duration=5.0), Step(step_id="2", title="B", description="d", order=2, estimated_duration=10.0)], 15.0),
    # 2. Parallel group (takes max)
    ([Step(step_id="1", title="A", description="d", order=1, estimated_duration=5.0, parallel_group="grp1"), Step(step_id="2", title="B", description="d", order=2, estimated_duration=12.0, parallel_group="grp1")], 12.0),
    # 3. Parallel + Sequential
    ([Step(step_id="1", title="A", description="d", order=1, estimated_duration=5.0, parallel_group="grp1"), Step(step_id="2", title="B", description="d", order=2, estimated_duration=12.0, parallel_group="grp1"), Step(step_id="3", title="C", description="d", order=3, estimated_duration=8.0)], 20.0),
    # 4. Zero/Negative Baseline duration conversion
    ([Step(step_id="1", title="A", description="d", order=1, estimated_duration=0.0)], 5.0),
    # 5. Multiple parallel groups
    ([Step(step_id="1", title="A", description="d", order=1, estimated_duration=5.0, parallel_group="grp1"), Step(step_id="2", title="B", description="d", order=2, estimated_duration=12.0, parallel_group="grp1"), Step(step_id="3", title="C", description="d", order=3, estimated_duration=4.0, parallel_group="grp2"), Step(step_id="4", title="D", description="d", order=4, estimated_duration=9.0, parallel_group="grp2")], 21.0),
]

@pytest.mark.parametrize("steps, expected_duration", DURATION_SCENARIOS)
def test_duration_estimator(steps: List[Step], expected_duration: float) -> None:
    assert DurationEstimator.estimate_plan_duration(steps) == expected_duration


# Fallback Generation Scenarios (5 tests)
FALLBACK_SCENARIOS = [
    # 1. Plan with one tool-required step
    ([Step(step_id="1", title="Send Email", description="d", order=1, tool_required="gmail")], 2),
    # 2. Plan with no tool-required steps
    ([Step(step_id="1", title="Local Action", description="d", order=1)], 1),
    # 3. Plan with multiple tool-required steps
    ([Step(step_id="1", title="Search", description="d", order=1, tool_required="calendar"), Step(step_id="2", title="Send", description="d", order=2, tool_required="gmail")], 4),
    # 4. Plan with mixed steps
    ([Step(step_id="1", title="Search", description="d", order=1, tool_required="calendar"), Step(step_id="2", title="Local", description="d", order=2)], 3),
    # 5. Empty steps plan fallback
    ([], 0),
]

@pytest.mark.parametrize("steps, expected_step_count", FALLBACK_SCENARIOS)
def test_plan_fallback_generator(steps: List[Step], expected_step_count: int) -> None:
    plan = Plan(goal="G", summary="S", steps=steps)
    fb_plan = PlanFallbackGenerator.generate_fallback_plan(plan)
    assert len(fb_plan.steps) == expected_step_count


# Rollback Step Scenarios (5 tests)
ROLLBACK_SCENARIOS = [
    # 1. Create step -> Delete rollback
    (Step(step_id="1", title="Create User Record", description="d", order=1), "Delete/Remove: User Record"),
    # 2. Add step -> Delete rollback
    (Step(step_id="1", title="Add task detail", description="d", order=1), "Delete/Remove: task detail"),
    # 3. Send step -> Sent folder rollback
    (Step(step_id="1", title="Send email status report", description="d", order=1), "Recall or delete draft from sent/outbox folder."),
    # 4. Update step -> Checkpoint rollback
    (Step(step_id="1", title="Update slot metadata", description="d", order=1), "Restore previous state value from checkpoint backups."),
    # 5. Read step -> No rollback
    (Step(step_id="1", title="Read inbox thread", description="d", order=1), None),
]

@pytest.mark.parametrize("step, expected_rollback", ROLLBACK_SCENARIOS)
def test_plan_rollback_generator(step: Step, expected_rollback: Optional[str]) -> None:
    PlanRollbackGenerator.populate_rollback_steps([step])
    assert step.rollback_step == expected_rollback


@pytest.mark.asyncio
async def test_plan_repository_operations(async_db_session: AsyncSession) -> None:
    """Verify PlanRepository saving, single loading, and batch loading queries (3 tests)."""
    repo = PlanRepository(async_db_session)
    user_id = uuid4()
    
    plan = Plan(
        goal="Test plan repository",
        summary="summary description details",
        steps=[
            Step(title="Step 1", description="desc 1", order=1, tool_required="calendar"),
            Step(title="Step 2", description="desc 2", order=2, dependencies=["Step 1"])
        ]
    )

    # Test 1: Save plan
    saved = await repo.save_plan(user_id, plan)
    assert saved.id is not None
    
    # Test 2: Get single plan joined with steps
    loaded = await repo.get_plan_with_steps(saved.id)
    assert loaded is not None
    assert len(loaded.steps) == 2
    assert loaded.steps[0].title == "Step 1"
    
    # Test 3: Get user plans batch loading
    user_plans = await repo.get_plans_by_user(user_id)
    assert len(user_plans) == 1
    assert user_plans[0].goal == "Test plan repository"


@pytest.mark.asyncio
async def test_planning_engine_pipeline(async_db_session: AsyncSession, default_context: BrainContext) -> None:
    """Verify PlanningEngine execute completes successfully and updates state (2 tests)."""
    import app.brain.planning.engine as engine_mod
    original_factory = engine_mod.async_session_factory
    engine_mod.async_session_factory = lambda: async_db_session

    try:
        mock_planner = GoalPlanner()
        mock_planner.generate_plan = AsyncMock(return_value=Plan(
            goal="Schedule calendar invite",
            summary="Schedule slot details",
            steps=[
                Step(step_id=str(uuid4()), title="Step 1", description="desc 1", order=1, tool_required="calendar"),
                Step(step_id=str(uuid4()), title="Step 2", description="desc 2", order=2, dependencies=["Step 1"])
            ]
        ))

        engine = PlanningEngine(planner=mock_planner)
        state = BrainState(context=default_context)
        message = AIMessage(role=MessageRole.USER, sender="user", recipient="ai", content="Schedule meeting.")
        state = state.update(conversation=state.conversation.model_copy(update={"incoming_message": message}))
        
        # Execute engine pipeline
        updated_state = await engine.execute(state)
        
        # Test 1: PlanningState populate assertion
        assert len(updated_state.planning.planned_actions) == 2
        assert updated_state.planning.execution_order[0] == updated_state.planning.planned_actions[0].action_id
        
        # Test 2: Validation assertion
        is_valid = await engine.validate(state)
        assert is_valid is True

    finally:
        engine_mod.async_session_factory = original_factory
