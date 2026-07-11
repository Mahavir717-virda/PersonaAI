import pytest
from datetime import datetime, timezone
from uuid import UUID, uuid4
from pydantic import ValidationError

from app.brain.schemas.state import (
    BrainState,
    BrainContext,
    UserProfileSnapshot,
    ExecutionContext,
    ConversationWindow,
    AIMessage,
    MessageRole,
    MemoryState,
    KnowledgeState,
    CommunicationIntelligence,
    EntityType,
    Entity,
    Task,
    TaskPriority,
    TaskStatus,
    PlanningState,
    PlannedAction,
    RAGState,
    SelectedDocument,
    ToolState,
    ToolCall,
    ToolStatus,
    ResponseGeneration,
    LearningState,
    RunMetadata,
    TokenBudget,
    ModelRouting,
    BaseEvent,
    EventType,
    EventState,
    AIDecision,
    SourceProvenance,
    AIReflection,
    NodeExecutionLog,
    RecoveryPlan,
)
from app.brain.engines.base import BrainEngine
from app.brain.events.brain_events import (
    MemoryRetrieved,
    MemoryStored,
    TaskCreated,
    ToolCalled,
    NodeCompleted,
)


@pytest.fixture
def default_context() -> BrainContext:
    """Fixture returning a standard BrainContext for testing."""
    profile = UserProfileSnapshot(
        user_id=uuid4(),
        timezone="America/New_York",
        language="en",
        permissions=["read", "write"],
    )
    return BrainContext(
        session_id=uuid4(),
        tenant_id="tenant-123",
        user_profile=profile,
    )


def test_default_brain_state_initialization(default_context: BrainContext) -> None:
    """Verify that BrainState initialized with context resolves standard default values."""
    state = BrainState(context=default_context)
    assert state.schema_version == "1.0.0"
    assert isinstance(state.context, BrainContext)
    assert isinstance(state.execution, ExecutionContext)
    assert isinstance(state.conversation, ConversationWindow)
    assert isinstance(state.memory, MemoryState)
    assert isinstance(state.knowledge, KnowledgeState)
    assert isinstance(state.communication_intelligence, CommunicationIntelligence)
    assert state.entities == []
    assert state.tasks == []
    assert isinstance(state.planning, PlanningState)
    assert isinstance(state.rag, RAGState)
    assert isinstance(state.tool_calling, ToolState)
    assert isinstance(state.response, ResponseGeneration)
    assert isinstance(state.learning, LearningState)
    assert isinstance(state.metadata, RunMetadata)
    assert isinstance(state.token_budget, TokenBudget)
    assert isinstance(state.model_routing, ModelRouting)
    assert isinstance(state.events, EventState)


def test_brain_state_immutability(default_context: BrainContext) -> None:
    """Verify that BrainState properties cannot be modified in place."""
    state = BrainState(context=default_context)
    with pytest.raises(ValidationError):
        state.execution = ExecutionContext(current_node="REASONING")


def test_brain_state_update_helper(default_context: BrainContext) -> None:
    """Verify that the state.update helper returns a new copy with modified fields."""
    state = BrainState(context=default_context)
    new_node = "REASONING"
    
    updated_state = state.update(execution=state.execution.model_copy(update={'current_node': new_node}))
    
    assert updated_state.execution.current_node == new_node
    # Old state remains unchanged
    assert state.execution.current_node != new_node


def test_conversation_and_message_schema(default_context: BrainContext) -> None:
    """Verify the conversation structure accepts incoming messages and preserves types."""
    message = AIMessage(
        role=MessageRole.USER,
        sender="user@gmail.com",
        recipient="persona@ai.com",
        content="Extract this task for tomorrow",
    )
    
    conv = ConversationWindow(
        incoming_message=message,
        current_conversation=[message],
    )
    
    state = BrainState(context=default_context, conversation=conv)
    assert state.conversation.incoming_message is not None
    assert state.conversation.incoming_message.content == "Extract this task for tomorrow"


def test_serialization_and_deserialization(default_context: BrainContext) -> None:
    """Verify the model can serialize to JSON/dict and deserialize back correctly."""
    state = BrainState(context=default_context)
    data = state.model_dump()
    deserialized = BrainState(**data)
    assert deserialized.context.session_id == state.context.session_id


def test_event_queue_handling(default_context: BrainContext) -> None:
    """Verify events can be tracked within the EventState queue."""
    event = BaseEvent(
        event_type=EventType.TASK_CREATED,
        source_node="TaskEngine",
        payload={"task_id": str(uuid4()), "title": "Review architectural changes"},
    )
    
    events_state = EventState(
        pending_events=[event],
    )
    
    state = BrainState(context=default_context, events=events_state)
    assert len(state.events.pending_events) == 1
    assert state.events.pending_events[0].event_type == EventType.TASK_CREATED


def test_decision_state_tracking(default_context: BrainContext) -> None:
    """Verify explainable AI decisions can be added to the state history."""
    decision = AIDecision(
        reason="Detected high priority email requesting immediate support.",
        confidence=0.95,
        selected_strategy="urgent_alert",
        selected_actions=["NotificationEngine"],
        risk_score=0.1,
    )
    
    state = BrainState(
        context=default_context,
        decisions=BrainState(
            context=default_context
        ).decisions.model_copy(update={
            "current_decision": decision,
            "decision_history": [decision],
        })
    )
    
    assert state.decisions.current_decision is not None
    assert state.decisions.current_decision.confidence == 0.95
    assert len(state.decisions.decision_history) == 1


# =====================================================================
# NEW STATE SCHEMAS & MOCK CONTRACT TESTS
# =====================================================================

def test_memory_lifecycle_categorization(default_context: BrainContext) -> None:
    """Verify categorization of human-like memory structures."""
    mem = MemoryState(
        working_memory=["Currently checking email attachments"],
        episodic_memory=["Received Gmail thread from John yesterday"],
        semantic_memory=["John is the project manager"],
        procedural_memory=["Send brief summaries on weekends"],
    )
    state = BrainState(context=default_context, memory=mem)
    assert state.memory.working_memory == ["Currently checking email attachments"]
    assert state.memory.episodic_memory == ["Received Gmail thread from John yesterday"]
    assert state.memory.semantic_memory == ["John is the project manager"]
    assert state.memory.procedural_memory == ["Send brief summaries on weekends"]


def test_provenance_and_node_logging(default_context: BrainContext) -> None:
    """Verify that source provenance and telemetry logs are structured correctly."""
    prov = SourceProvenance(
        source_platform="gmail",
        source_thread_id="thread_abc",
        source_message_id="msg_123",
    )
    
    log = NodeExecutionLog(
        node_name="RAGEngine",
        duration_ms=145.2,
        success=True,
    )
    
    state = BrainState(
        context=default_context,
        metadata=BrainState(context=default_context).metadata.model_copy(update={
            "node_execution_logs": [log]
        })
    )
    
    assert state.metadata.node_execution_logs[0].node_name == "RAGEngine"
    assert state.metadata.node_execution_logs[0].duration_ms == 145.2
    assert state.metadata.node_execution_logs[0].success is True


def test_strongly_typed_brain_events() -> None:
    """Verify that typed BrainEvents initialize and preserve custom payloads."""
    evt = TaskCreated(
        source_node="TaskEngine",
        task_id=uuid4(),
        title="Deploy PersonaAI",
    )
    assert evt.source_node == "TaskEngine"
    assert evt.title == "Deploy PersonaAI"
    assert isinstance(evt.event_id, UUID)


@pytest.mark.asyncio
async def test_brain_engine_contract_compliance(default_context: BrainContext) -> None:
    """Verify mock engine subclassing BrainEngine contract executes and behaves correctly."""
    class MockMemoryEngine(BrainEngine):
        @property
        def name(self) -> str:
            return "MockMemoryEngine"

        async def execute(self, state: BrainState) -> BrainState:
            # Simulate a memory retrieval write
            new_memory = state.memory.model_copy(update={
                "working_memory": ["New retrieved state info"]
            })
            return state.update(memory=new_memory)

        async def validate(self, state: BrainState) -> bool:
            return state.context.user_profile.user_id is not None

        async def rollback(self, state: BrainState) -> BrainState:
            return state

    engine = MockMemoryEngine()
    state = BrainState(context=default_context)
    
    assert engine.name == "MockMemoryEngine"
    assert await engine.validate(state) is True
    
    next_state = await engine.execute(state)
    assert next_state.memory.working_memory == ["New retrieved state info"]
