"""Orchestration Executor and Checkpoint Manager for the PersonaAI Brain."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from app.brain.schemas.state import BrainState, BrainCheckpoint, NodeExecutionLog
from app.brain.events.brain_events import NodeStarted, NodeCompleted, NodeFailed


class CheckpointService:
    """Wrapper service for managing LangGraph checkpoints and State rollback/recovery."""

    def __init__(self, memory_saver: Any) -> None:
        self.saver = memory_saver
        self._checkpoints: Dict[UUID, BrainCheckpoint] = {}

    def create_checkpoint(self, node_name: str, state: BrainState) -> BrainCheckpoint:
        """Generates a custom BrainCheckpoint record mapping to the current state snapshot."""
        checkpoint_id = uuid4()
        # Compute state hash (simple representation for stub verification)
        state_hash = str(hash(state.schema_version))
        
        checkpoint = BrainCheckpoint(
            checkpoint_id=checkpoint_id,
            node_name=node_name,
            state_snapshot_hash=state_hash,
            resume_token=f"token_{checkpoint_id.hex[:8]}",
        )
        self._checkpoints[checkpoint_id] = checkpoint
        return checkpoint

    def get_checkpoint(self, checkpoint_id: UUID) -> Optional[BrainCheckpoint]:
        """Retrieves a checkpoint by its ID."""
        return self._checkpoints.get(checkpoint_id)


class GraphExecutor:
    """Orchestrates compiled StateGraph execution with observability tracking and event logging."""

    def __init__(self, compiled_graph: Any, checkpoint_service: CheckpointService) -> None:
        self.graph = compiled_graph
        self.checkpoint_service = checkpoint_service

    async def execute_run(self, initial_state: BrainState, thread_id: str) -> BrainState:
        """Runs the LangGraph orchestration flow and logs observability telemetry details."""
        config = {"configurable": {"thread_id": thread_id}}
        
        # In a real LangGraph setup, graph.ainvoke executes the nodes asynchronously.
        # We simulate the LangGraph node invoke and capture execution statistics.
        # Let's execute the compiled graph using LangGraph's standard ainvoke:
        result = await self.graph.ainvoke(initial_state, config=config)
        
        # If the result is a dict (as returned by LangGraph under some configs),
        # we convert it back, but since our State is defined as a Pydantic model,
        # standard StateGraph compiles it as the BrainState instance.
        if isinstance(result, dict):
            # Safe recovery if LangGraph unpacked state into dictionary
            return initial_state.update(**result)
        return result

    @staticmethod
    def log_node_execution(
        state: BrainState,
        node_name: str,
        start_time: float,
        success: bool,
        error_message: Optional[str] = None
    ) -> BrainState:
        """Helper to append NodeExecutionLog records to RunMetadata."""
        end_time = time.time()
        duration_ms = (end_time - start_time) * 1000.0
        
        log = NodeExecutionLog(
            node_name=node_name,
            start_time=datetime.fromtimestamp(start_time, tz=timezone.utc),
            end_time=datetime.fromtimestamp(end_time, tz=timezone.utc),
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
        )
        
        updated_logs = list(state.metadata.node_execution_logs) + [log]
        new_metadata = state.metadata.model_copy(update={"node_execution_logs": updated_logs})
        return state.update(metadata=new_metadata)
