"""Strongly typed events for the PersonaAI Brain communication layer.

All engine components produce and consume these event objects to decouple
execution nodes and enable clean message-driven agent orchestration.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from app.brain.schemas.state import PlatformConnector


class BrainEvent(BaseModel):
    """Foundational class for all Brain events."""
    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Event publishing timestamp.")
    source_node: str = Field(..., description="The name of the engine node that published the event.")
    correlation_id: Optional[UUID] = Field(default=None, description="Linked execution run or flow ID.")


# =====================================================================
# MEMORY EVENTS
# =====================================================================

class MemoryRetrieved(BrainEvent):
    """Fired when memories are successfully retrieved for context ingestion."""
    query: str = Field(..., description="Query used to search memory stores.")
    memories: List[str] = Field(..., description="Retrieved raw memory strings.")
    scores: Dict[str, float] = Field(default_factory=dict, description="Similarity scores per memory.")


class MemoryStored(BrainEvent):
    """Fired when a new episodic or semantic memory is persisted."""
    memory_id: UUID = Field(..., description="Identifier of the stored memory.")
    content: str = Field(..., description="Serialized content of the memory.")
    memory_type: str = Field(..., description="working, episodic, semantic, or procedural.")


# =====================================================================
# KNOWLEDGE GRAPH EVENTS
# =====================================================================

class KnowledgeUpdated(BrainEvent):
    """Fired when entities or relationships are created/updated in the graph."""
    updated_entities: List[str] = Field(default_factory=list, description="IDs of updated nodes.")
    updated_relations: List[str] = Field(default_factory=list, description="IDs of updated edges.")
    source_platform: PlatformConnector = Field(..., description="Context platform source.")


# =====================================================================
# TASK EVENTS
# =====================================================================

class TaskCreated(BrainEvent):
    """Fired when a new task is extracted from the user conversation."""
    task_id: UUID = Field(..., description="Extracted task ID.")
    title: str = Field(..., description="Action title.")
    deadline: Optional[datetime] = Field(default=None, description="Assigned completion date.")
    owner: Optional[str] = Field(default=None, description="Assigned execution actor.")


class TaskCompleted(BrainEvent):
    """Fired when an active task is marked as COMPLETED in task state."""
    task_id: UUID = Field(..., description="Target task ID.")
    completion_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =====================================================================
# PLANNING EVENTS
# =====================================================================

class PlanGenerated(BrainEvent):
    """Fired when a sequence of planned actions is determined."""
    actions: List[str] = Field(..., description="Sequence of plan step names.")
    next_action: str = Field(..., description="Immediate next task scheduled.")


# =====================================================================
# RESPONSE EVENTS
# =====================================================================

class ResponseGenerated(BrainEvent):
    """Fired when a generator engine yields a candidate or final response."""
    raw_response: str = Field(..., description="Raw text response.")
    formatted_response: Optional[str] = Field(default=None, description="Post-processed response format.")
    tokens_used: int = Field(..., description="Tokens consumed during model generation.")


# =====================================================================
# TOOL EVENTS
# =====================================================================

class ToolCalled(BrainEvent):
    """Fired when a registered tool starts executing."""
    call_id: str = Field(..., description="Unique call ID.")
    tool_name: str = Field(..., description="Name of the target tool.")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Supplied input arguments.")


class ToolFailed(BrainEvent):
    """Fired when tool execution throws an exception."""
    call_id: str = Field(..., description="Unique call ID.")
    tool_name: str = Field(..., description="Name of the target tool.")
    error_message: str = Field(..., description="Trace logs or error reason.")


# =====================================================================
# EXECUTION FLOW LOGGING EVENTS
# =====================================================================

class NodeStarted(BrainEvent):
    """Fired when a StateGraph engine node begins executing."""
    node_name: str = Field(..., description="Name of the node.")


class NodeCompleted(BrainEvent):
    """Fired when a StateGraph engine node completes processing successfully."""
    node_name: str = Field(..., description="Name of the node.")
    duration_ms: float = Field(..., description="Node processing latency.")


class NodeFailed(BrainEvent):
    """Fired when a StateGraph engine node throws an unhandled error."""
    node_name: str = Field(..., description="Name of the node.")
    error_message: str = Field(..., description="Exception error string.")


# =====================================================================
# LEARNING EVENTS
# =====================================================================

class LearningCompleted(BrainEvent):
    """Fired when the learning engine completes write-back tasks."""
    persisted_memories_count: int = Field(..., description="Number of new long-term memories saved.")
    preference_keys_modified: List[str] = Field(default_factory=list, description="Preferences updated.")
