import pytest
from uuid import uuid4
from langgraph.checkpoint.memory import MemorySaver

from app.brain.schemas.state import BrainState, BrainContext, UserProfileSnapshot, AIReflection
from app.brain.orchestrator.dependencies import BrainContainer
from app.brain.orchestrator.executor import GraphExecutor, CheckpointService
from app.brain.orchestrator.graph import build_brain_graph


@pytest.fixture
def default_context() -> BrainContext:
    """Fixture returning a standard BrainContext for testing."""
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


def test_brain_container_registration() -> None:
    """Verify DI container registers default engines and supports overrides."""
    container = BrainContainer()
    assert "memory" in container.list_registered_engines()
    assert "knowledge" in container.list_registered_engines()
    assert "rag" in container.list_registered_engines()
    
    # Verify we can fetch engine instances
    memory_engine = container.get("memory")
    assert memory_engine.name == "memory"


def test_checkpoint_service_management(default_context: BrainContext) -> None:
    """Verify that CheckpointService generates and retrieves states correctly."""
    memory_saver = MemorySaver()
    service = CheckpointService(memory_saver=memory_saver)
    
    state = BrainState(context=default_context)
    checkpoint = service.create_checkpoint(node_name="RAGEngine", state=state)
    
    assert checkpoint.node_name == "RAGEngine"
    assert service.get_checkpoint(checkpoint.checkpoint_id) == checkpoint


@pytest.mark.asyncio
async def test_full_graph_execution(default_context: BrainContext) -> None:
    """Verify compiled StateGraph executes successfully and records telemetry logs."""
    container = BrainContainer()
    memory_saver = MemorySaver()
    compiled_graph = build_brain_graph(container, checkpointer=memory_saver)
    
    service = CheckpointService(memory_saver=memory_saver)
    executor = GraphExecutor(compiled_graph=compiled_graph, checkpoint_service=service)
    
    # Initialize state with a standard context
    initial_state = BrainState(context=default_context)
    thread_id = "test_thread_1"
    
    final_state = await executor.execute_run(initial_state, thread_id=thread_id)
    
    # Verify execution ran through nodes
    assert len(final_state.metadata.node_execution_logs) > 0
    # Ensure sequential flow transitions: memory node was executed
    executed_nodes = [log.node_name for log in final_state.metadata.node_execution_logs]
    assert "memory" in executed_nodes
    assert "knowledge" in executed_nodes
    assert "reasoning" in executed_nodes
    assert "response" in executed_nodes
    assert "learning" in executed_nodes


@pytest.mark.asyncio
async def test_routing_greeting_skips_knowledge(default_context: BrainContext) -> None:
    """Verify route_after_memory routes greeting intents straight to response, skipping search."""
    container = BrainContainer()
    memory_saver = MemorySaver()
    compiled_graph = build_brain_graph(container, checkpointer=memory_saver)
    
    service = CheckpointService(memory_saver=memory_saver)
    executor = GraphExecutor(compiled_graph=compiled_graph, checkpoint_service=service)
    
    # Initialize state with a greeting intent
    initial_state = BrainState(context=default_context)
    initial_state = initial_state.update(
        communication_intelligence=initial_state.communication_intelligence.model_copy(update={
            "intent": "greeting"
        })
    )
    
    final_state = await executor.execute_run(initial_state, thread_id="greeting_thread")
    executed_nodes = [log.node_name for log in final_state.metadata.node_execution_logs]
    
    assert "memory" in executed_nodes
    assert "response" in executed_nodes
    # Knowledge was skipped due to routing logic
    assert "knowledge" not in executed_nodes
