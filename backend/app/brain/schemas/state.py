"""Central BrainState and nested models for PersonaAI's LangGraph StateGraph.

This module defines the complete, strongly typed state architecture that flows
through the AI Communication Operating System's graph engines. It guarantees
type safety, immutability where practical, serialization, and ease of tracing.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# ENUMS
# =====================================================================

class PlatformConnector(str, Enum):
    """Supported communication platforms and connectors."""
    GMAIL = "gmail"
    WHATSAPP = "whatsapp"
    SLACK = "slack"
    DISCORD = "discord"
    TEAMS = "teams"
    OUTLOOK = "outlook"
    WEB = "web"
    CUSTOM = "custom"


class TaskPriority(str, Enum):
    """Task urgency levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Workflow state for extracted tasks."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class EntityType(str, Enum):
    """Supported semantic entity classifications."""
    PERSON = "person"
    ORGANIZATION = "organization"
    PROJECT = "project"
    TASK = "task"
    DATE = "date"
    TIME = "time"
    LOCATION = "location"
    MONEY = "money"
    MEETING = "meeting"
    DEADLINE = "deadline"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    CUSTOM = "custom"


class ToolStatus(str, Enum):
    """Execution status for invoked tools."""
    PENDING = "pending"
    SUCCESS = "success"
    FAILURE = "failure"


class MessageRole(str, Enum):
    """Standardized roles for AI message logs, aligned with LLM APIs."""
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class EventType(str, Enum):
    """Supported event classifications for the inner-engine event queue."""
    MEMORY_CREATED = "MemoryCreated"
    TASK_CREATED = "TaskCreated"
    REMINDER_CREATED = "ReminderCreated"
    KNOWLEDGE_UPDATED = "KnowledgeUpdated"
    SUMMARY_GENERATED = "SummaryGenerated"
    CUSTOM = "CustomEvent"


class MemoryLifecycleStage(str, Enum):
    """Lifecycle stages for memories from creation to deletion."""
    CREATED = "created"
    WORKING = "working"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    LONG_TERM = "long_term"
    ARCHIVED = "archived"
    COMPRESSED = "compressed"
    DELETED = "deleted"


# =====================================================================
# SOURCE PROVENANCE (Audit Trail Tracking)
# =====================================================================

class SourceProvenance(BaseModel):
    """Metadata detailing the origin and audit trail of facts or memories."""
    model_config = ConfigDict(frozen=True)

    source_platform: PlatformConnector = Field(default=PlatformConnector.CUSTOM, description="Platform source (e.g., Gmail, Slack).")
    source_thread_id: Optional[str] = Field(default=None, description="Thread identifier from the platform.")
    source_message_id: Optional[str] = Field(default=None, description="Message identifier from the platform.")
    segment_locator: Optional[str] = Field(default=None, description="Precise locator tag within message (e.g. paragraph offset).")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of when the source was authored.")


# =====================================================================
# AI MESSAGES (Modern LLM Framework Compatible)
# =====================================================================

class AIMessage(BaseModel):
    """Base AI message model for conversation streams."""
    model_config = ConfigDict(frozen=True)

    message_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique message ID.")
    role: MessageRole = Field(..., description="Role of the message author.")
    content: str = Field(..., description="Text content or payload representation.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp of the message.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom metadata attributes.")


class SystemMessage(AIMessage):
    """Instructions or guardrails sent to guide the model's behavior."""
    role: MessageRole = MessageRole.SYSTEM


class DeveloperMessage(AIMessage):
    """System-level prompts or developer overrides that shape the graph lifecycle."""
    role: MessageRole = MessageRole.DEVELOPER


class UserMessage(AIMessage):
    """Incoming communication from the user."""
    role: MessageRole = MessageRole.USER


class AssistantMessage(AIMessage):
    """Responses generated by internal AI engine models."""
    role: MessageRole = MessageRole.ASSISTANT


class ToolMessage(AIMessage):
    """Execution logs or outputs returned by tools, linked back to an assistant request."""
    role: MessageRole = MessageRole.TOOL
    tool_call_id: str = Field(..., description="Identifier linking this message to the original tool request.")


# =====================================================================
# USER PROFILE SNAPSHOT (CACHED USER CONTEXT)
# =====================================================================

class UserProfileSnapshot(BaseModel):
    """Cached user configuration snapshot to prevent DB lookups at every node."""
    model_config = ConfigDict(frozen=True)

    user_id: UUID = Field(..., description="The user's unique identifier.")
    profile_details: Dict[str, str] = Field(default_factory=dict, description="Basic profile information.")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="AI behaviors and custom preferences.")
    timezone: str = Field(default="UTC", description="IANA Timezone format.")
    language: str = Field(default="en", description="Preferred language (ISO 639-1).")
    permissions: List[str] = Field(default_factory=list, description="Assigned user scopes or authorization flags.")


# =====================================================================
# BRAIN CONTEXT (Static / Infrequently Changing Context)
# =====================================================================

class BrainContext(BaseModel):
    """Read-only or static environment variables for the current run.

    Provides tenant identification, tenant authentication details, session scoping,
    and runtime mode variables that remain constant throughout the graph traversal.
    """
    model_config = ConfigDict(frozen=True)

    session_id: UUID = Field(default_factory=uuid4, description="Scoping ID for the active orchestrator lifecycle.")
    tenant_id: str = Field(default="default", description="Multi-tenant identifier.")
    connector: PlatformConnector = Field(default=PlatformConnector.CUSTOM, description="Active channel connector.")
    platform: str = Field(default="generic", description="Target workspace details.")
    graph_version: str = Field(default="1.0.0", description="Version of the active graph definition.")
    execution_mode: str = Field(default="standard", description="standard, validation, or batch.")
    debug_mode: bool = Field(default=False, description="Enables deep telemetry and node timing capture.")
    feature_flags: Dict[str, bool] = Field(default_factory=dict, description="Active product flags for this execution.")
    authentication_context: Dict[str, Any] = Field(default_factory=dict, description="OAuth or API token caches.")
    user_profile: UserProfileSnapshot = Field(..., description="Cached snapshot of the executing user context.")


# =====================================================================
# ERROR RECOVERY PLAN
# =====================================================================

class RecoveryPlan(BaseModel):
    """Defines automated recovery steps to take when a node encounters an execution error."""
    model_config = ConfigDict(frozen=True)

    retry_count: int = Field(default=0, description="Number of retries attempted for this recovery step.")
    fallback_model: Optional[str] = Field(default=None, description="Alternative model to route to on failure.")
    fallback_tool: Optional[str] = Field(default=None, description="Alternative tool parameter mapping.")
    skip_node: bool = Field(default=False, description="Whether to ignore this engine's failure and skip forward.")
    abort: bool = Field(default=False, description="If true, immediately halts state orchestration and raises failure.")


# =====================================================================
# EXECUTION CONTEXT (In-Graph Routing Tracking)
# =====================================================================

class ExecutionContext(BaseModel):
    """Graph routing state detailing node entry, visited paths, and retries."""
    model_config = ConfigDict(frozen=True)

    current_node: str = Field(default="START", description="The active node processing the state.")
    previous_node: Optional[str] = Field(default=None, description="The node that immediately preceded this one.")
    next_node: Optional[str] = Field(default=None, description="The target node to execute next.")
    visited_nodes: List[str] = Field(default_factory=list, description="Ordered trace of executed nodes.")
    agent_states: Dict[str, str] = Field(default_factory=dict, description="Current statuses of active agents (e.g. Planning: WAITING).")
    branch: Optional[str] = Field(default=None, description="Branch execution label if routing dynamically.")
    execution_depth: int = Field(default=0, description="Depth counter to prevent recursive infinite loops.")
    checkpoint_id: Optional[UUID] = Field(default=None, description="LangGraph checkpoint linkage.")
    graph_version: str = Field(default="1.0.0", description="Target execution graph configuration version.")
    recovery_plan: RecoveryPlan = Field(default_factory=RecoveryPlan, description="Strategy for fault recovery.")


# =====================================================================
# CONVERSATION WINDOW (Context Optimization)
# =====================================================================

class Attachment(BaseModel):
    """Metadata representing files or assets attached to a message."""
    model_config = ConfigDict(frozen=True)

    attachment_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID for the attachment.")
    filename: str = Field(..., description="Name of the file.")
    content_type: str = Field(..., description="MIME type.")
    size_bytes: int = Field(..., description="Size in bytes.")
    storage_uri: str = Field(..., description="Internal storage URL.")


class ConversationWindow(BaseModel):
    """Chronological conversation boundaries to prevent token overflow."""
    model_config = ConfigDict(frozen=True)

    incoming_message: Optional[AIMessage] = Field(default=None, description="The message triggering this run.")
    attachments: List[Attachment] = Field(default_factory=list, description="Attachments included in this message.")
    current_conversation: List[AIMessage] = Field(default_factory=list, description="Active context messages.")
    compressed_conversation: Optional[str] = Field(default=None, description="Summarized past history context.")
    archived_conversation: List[AIMessage] = Field(default_factory=list, description="Historical messages sliced out of local context window.")


# =====================================================================
# RETRIEVAL TRACE & RAG STATE
# =====================================================================

class SelectedDocument(BaseModel):
    """Record of a source document chunk matched and contextually utilized."""
    model_config = ConfigDict(frozen=True)

    document_id: str = Field(..., description="Identifier of the source chunk.")
    content: str = Field(..., description="Text content extracted.")
    similarity_score: float = Field(..., description="Initial vector distance match score.")
    reranking_score: float = Field(..., description="Re-ranked relevance score (if applicable).")
    final_score: float = Field(..., description="Synthesized routing rank score.")
    selection_reason: str = Field(..., description="Why the generator or planner selected this specific document.")
    citation: Optional[str] = Field(default=None, description="Formal attribution details.")
    provenance: Optional[SourceProvenance] = Field(default=None, description="Audit trace to source connector.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tags.")


class RejectedDocument(BaseModel):
    """Telemetry records of matched chunks filtered out during execution."""
    model_config = ConfigDict(frozen=True)

    document_id: str = Field(..., description="Identifier.")
    similarity_score: float = Field(..., description="Initial vector distance match score.")
    rejection_reason: str = Field(..., description="E.g., below threshold, redundant, or token overflow.")


class RAGState(BaseModel):
    """Retrieval parameters, matches, and detailed trace logs."""
    model_config = ConfigDict(frozen=True)

    query: Optional[str] = Field(default=None, description="Formulated query string.")
    retrieved_documents: List[SelectedDocument] = Field(default_factory=list, description="Raw matches found.")
    reranked_documents: List[SelectedDocument] = Field(default_factory=list, description="Top results after ranking model application.")
    rejected_documents: List[RejectedDocument] = Field(default_factory=list, description="Telemetry logs of matched but filtered documents.")
    citations: List[str] = Field(default_factory=list, description="Attributions list.")
    vector_search_score: float = Field(default=0.0, description="Maximum search score matching the query.")
    confidence: float = Field(default=0.0, description="Aggregate RAG retrieval confidence (0.0 to 1.0).")


# =====================================================================
# EVENT QUEUE (Inner-Engine Messaging)
# =====================================================================

class BaseEvent(BaseModel):
    """Unified engine event payload."""
    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4, description="Unique event identifier.")
    event_type: Union[EventType, str] = Field(..., description="Classification category.")
    source_node: str = Field(..., description="Engine node that published this event.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp.")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Target data properties.")


class EventState(BaseModel):
    """Inner-engine event queues representing pending, completed, or failed tasks."""
    model_config = ConfigDict(frozen=True)

    pending_events: List[BaseEvent] = Field(default_factory=list, description="Events waiting to be processed by engines.")
    completed_events: List[BaseEvent] = Field(default_factory=list, description="Successful event logs.")
    failed_events: List[BaseEvent] = Field(default_factory=list, description="Errors or failed event publications.")


# =====================================================================
# AI DECISIONS (Explainable AI Logic)
# =====================================================================

class AIDecision(BaseModel):
    """Traceable decision metrics compiled by routing or reasoning engines."""
    model_config = ConfigDict(frozen=True)

    decision_id: UUID = Field(default_factory=uuid4, description="Unique decision execution ID.")
    reason: str = Field(..., description="Structured explanation detailing why the action was selected.")
    confidence: float = Field(..., description="Evaluated confidence score (0.0 to 1.0).")
    selected_strategy: str = Field(..., description="Selected routing strategy or path.")
    selected_memory: List[str] = Field(default_factory=list, description="IDs of historical memories referenced.")
    selected_tool: List[str] = Field(default_factory=list, description="Names of tools planned for execution.")
    selected_documents: List[str] = Field(default_factory=list, description="IDs of documents injected into prompt contexts.")
    selected_actions: List[str] = Field(default_factory=list, description="Downstream execution nodes chosen.")
    risk_score: float = Field(default=0.0, description="Estimated safety or risk level (0.0 to 1.0).")


class DecisionState(BaseModel):
    """Reasoning traces active in the current execution loop."""
    model_config = ConfigDict(frozen=True)

    current_decision: Optional[AIDecision] = Field(default=None, description="Active routing decision details.")
    decision_history: List[AIDecision] = Field(default_factory=list, description="Chronological decisions trace.")


# =====================================================================
# ENGINE SUB-STATES
# =====================================================================

class MemoryState(BaseModel):
    """Episodic, working, and semantic memories retrieved or updated."""
    model_config = ConfigDict(frozen=True)

    working_memory: List[str] = Field(default_factory=list, description="Immediate workspace contexts (e.g. current loop context).")
    episodic_memory: List[str] = Field(default_factory=list, description="Time-bound historical interaction events (e.g. yesterday's Gmail thread).")
    semantic_memory: List[str] = Field(default_factory=list, description="Conceptual facts and associations (e.g. 'John is manager').")
    procedural_memory: List[str] = Field(default_factory=list, description="Skills, constraints, and process rules (e.g. 'User prefers concise replies').")
    
    retrieved_memories: List[str] = Field(default_factory=list, description="Flat collection of raw retrieved memory nodes.")
    memory_score: Dict[str, float] = Field(default_factory=dict, description="Similarity scores mapped to retrieve keys.")
    short_term: List[str] = Field(default_factory=list, description="Session-level transient records.")
    long_term: List[str] = Field(default_factory=list, description="Global persistent records.")
    retrieval_reasons: Dict[str, str] = Field(default_factory=dict, description="Telemetry justifications for retrieving each memory.")
    lifecycle_stages: Dict[str, MemoryLifecycleStage] = Field(default_factory=dict, description="Active lifecycle stage per memory key.")
    links: Dict[str, List[str]] = Field(default_factory=dict, description="Linked memories associated with each memory key.")
    compiled_context: str = Field(default="", description="Compiled memory context string for prompt injection.")
    confidence: float = Field(default=1.0, description="Memory retrieval confidence score.")


class GraphNode(BaseModel):
    """Entity node details in the Knowledge Graph with version history and provenance trace."""
    model_config = ConfigDict(frozen=True)

    node_id: str = Field(..., description="Unique ID.")
    label: str = Field(..., description="Name.")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Attributes.")
    version: int = Field(default=1, description="Snapshot version tracking incremental changes.")
    superseded_by_id: Optional[str] = Field(default=None, description="ID of node that superseded this version.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: Optional[SourceProvenance] = Field(default=None, description="Source provenance details.")


class GraphRelationship(BaseModel):
    """Directed connection in the Knowledge Graph with version history and provenance trace."""
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(..., description="Source ID.")
    target_id: str = Field(..., description="Target ID.")
    relation_type: str = Field(..., description="Relation predicate.")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Relation attributes.")
    version: int = Field(default=1, description="Relationship schema version.")
    superseded_by_id: Optional[str] = Field(default=None, description="Linkage to newer version of relationship.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance: Optional[SourceProvenance] = Field(default=None, description="Source provenance details.")


class KnowledgeState(BaseModel):
    """Knowledge Graph sub-graphs retrieved."""
    model_config = ConfigDict(frozen=True)

    retrieved_facts: List[str] = Field(default_factory=list, description="Factual records.")
    entities: List[GraphNode] = Field(default_factory=list, description="Sub-graph nodes.")
    relationships: List[GraphRelationship] = Field(default_factory=list, description="Sub-graph edges.")
    graph_nodes: List[str] = Field(default_factory=list, description="Raw node text representation.")
    confidence: float = Field(default=1.0, description="Knowledge extraction or search confidence score.")


class CommunicationIntelligence(BaseModel):
    """Intent and sentiment extraction scores."""
    model_config = ConfigDict(frozen=True)

    intent: str = Field(default="unknown", description="Primary intent classification.")
    emotion: str = Field(default="neutral", description="Detected emotional state.")
    urgency: str = Field(default="low", description="Evaluated urgency level.")
    priority: str = Field(default="medium", description="Evaluated execution priority.")
    tone: str = Field(default="neutral", description="Detected tone.")
    category: str = Field(default="general", description="Detected category.")
    requires_reply: bool = Field(default=False, description="Whether interaction requires a reply.")
    contains_task: bool = Field(default=False, description="Whether interaction contains tasks.")
    contains_deadline: bool = Field(default=False, description="Whether interaction contains deadlines.")
    contains_decision: bool = Field(default=False, description="Whether interaction contains decisions.")
    contains_meeting: bool = Field(default=False, description="Whether interaction contains meetings.")
    confidence: float = Field(default=0.0, description="Classification confidence (0.0 to 1.0).")


class Entity(BaseModel):
    """Extracted text entity information."""
    model_config = ConfigDict(frozen=True)

    entity_type: EntityType = Field(..., description="Entity classification.")
    value: str = Field(..., description="Text segment.")
    start_char: int = Field(..., description="Start character offset.")
    end_char: int = Field(..., description="End character offset.")
    confidence: float = Field(default=1.0, description="Extraction confidence (0.0 to 1.0).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata tags.")


class Task(BaseModel):
    """Extracted action item task representation."""
    model_config = ConfigDict(frozen=True)

    task_id: UUID = Field(default_factory=uuid4, description="Unique ID.")
    title: str = Field(..., description="Name.")
    description: Optional[str] = Field(default=None, description="Details.")
    deadline: Optional[datetime] = Field(default=None, description="Deadline timestamp.")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task urgency.")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Task status.")
    owner: Optional[str] = Field(default=None, description="Owner identifier.")
    confidence: float = Field(default=1.0, description="Extraction confidence (0.0 to 1.0).")


class PlannedAction(BaseModel):
    """Planned task action."""
    model_config = ConfigDict(frozen=True)

    action_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique ID.")
    name: str = Field(..., description="Action node identifier.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Arguments.")
    description: Optional[str] = Field(default=None, description="Self-documentation.")


class PlanningState(BaseModel):
    """Planned sequences generated by the planner."""
    model_config = ConfigDict(frozen=True)

    planned_actions: List[PlannedAction] = Field(default_factory=list, description="Sequence of actions.")
    execution_order: List[str] = Field(default_factory=list, description="Action execution order IDs.")
    dependencies: Dict[str, List[str]] = Field(default_factory=dict, description="Dependency maps.")
    next_best_action: Optional[PlannedAction] = Field(default=None, description="Recommended immediate action.")
    confidence: float = Field(default=1.0, description="Planning confidence score.")


# =====================================================================
# TOOL STATE & TOOL REGISTRY
# =====================================================================

class ToolCall(BaseModel):
    """Record of a tool invocation."""
    model_config = ConfigDict(frozen=True)

    call_id: str = Field(default_factory=lambda: str(uuid4()), description="Call identifier.")
    tool_name: str = Field(..., description="Target tool identifier.")
    input_data: Dict[str, Any] = Field(default_factory=dict, description="Arguments.")
    output_data: Optional[Dict[str, Any]] = Field(default=None, description="Response payload.")
    error_message: Optional[str] = Field(default=None, description="Stack trace or error payload.")
    status: ToolStatus = Field(default=ToolStatus.PENDING, description="Execution status.")


class ToolState(BaseModel):
    """Active tool registry and history logs for current run."""
    model_config = ConfigDict(frozen=True)

    available_tools: List[str] = Field(default_factory=list, description="List of all tools discovered on host environment.")
    registered_tools: List[str] = Field(default_factory=list, description="All tools currently loaded in the agent run.")
    enabled_tools: List[str] = Field(default_factory=list, description="Sub-selection of tools active for current node reasoning.")
    disabled_tools: List[str] = Field(default_factory=list, description="Explicitly blacklisted tools.")
    tool_capabilities: Dict[str, List[str]] = Field(default_factory=dict, description="Capabilities/Tags defined per tool (e.g. Gmail: ['read', 'send']).")

    tool_inputs: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Arguments maps.")
    tool_outputs: Dict[str, Any] = Field(default_factory=dict, description="Outputs maps.")
    tool_errors: Dict[str, str] = Field(default_factory=dict, description="Error messages maps.")
    history: List[ToolCall] = Field(default_factory=list, description="Execution history.")


# =====================================================================
# RESPONSE GENERATION & REFLECTION
# =====================================================================

class AIReflection(BaseModel):
    """Evaluations performed post-generation to check for accuracy, context limits, and gaps."""
    model_config = ConfigDict(frozen=True)

    is_answer_complete: bool = Field(default=True, description="Evaluates whether the user's intent was fully addressed.")
    is_retrieval_sufficient: bool = Field(default=True, description="Checks if the injected chunks provided enough details.")
    needs_more_search: bool = Field(default=False, description="Triggers additional search cycles if chunks were lacking.")
    needs_another_tool: bool = Field(default=False, description="Tells planner that a different tool should be scheduled.")
    needs_clarification: bool = Field(default=False, description="If true, requests clarification input from user instead of responding.")


class ResponseGeneration(BaseModel):
    """LLM inputs and generation results."""
    model_config = ConfigDict(frozen=True)

    system_prompt: Optional[str] = Field(default=None, description="System instructions.")
    context: Optional[str] = Field(default=None, description="Context payload.")
    final_prompt: Optional[str] = Field(default=None, description="Full prompt.")
    llm_response: Optional[str] = Field(default=None, description="Raw response text.")
    formatted_response: Optional[str] = Field(default=None, description="Formatted response text.")
    reflection: AIReflection = Field(default_factory=AIReflection, description="Self-reflection telemetry.")
    confidence: float = Field(default=1.0, description="Response generation confidence score (0.0 to 1.0).")


# =====================================================================
# LEARNING STATE
# =====================================================================

class LearningState(BaseModel):
    """Learning updates scheduled for write-back."""
    model_config = ConfigDict(frozen=True)

    new_memories: List[str] = Field(default_factory=list, description="Episodic memories to save.")
    updated_preferences: Dict[str, Any] = Field(default_factory=dict, description="Preference updates.")
    feedback: Optional[str] = Field(default=None, description="Feedback signal.")
    memory_updates: List[Dict[str, Any]] = Field(default_factory=list, description="Updates to memories.")
    knowledge_updates: List[Dict[str, Any]] = Field(default_factory=list, description="Updates to graph.")


# =====================================================================
# TOKEN BUDGET
# =====================================================================

class TokenBudget(BaseModel):
    """Active token limit tracking."""
    model_config = ConfigDict(frozen=True)

    current_tokens: int = Field(default=0, description="Tokens currently consumed by active structures.")
    remaining_tokens: int = Field(default=128000, description="Context tokens remaining before limit exhaustion.")
    reserved_tokens: int = Field(default=4096, description="Reserved token buffer size for responses.")
    compression_required: bool = Field(default=False, description="Flag indicating context compression is required.")


# =====================================================================
# MODEL ROUTING
# =====================================================================

class ModelRouting(BaseModel):
    """Configuration for LLM targeting per engine or node execution."""
    model_config = ConfigDict(frozen=True)

    selected_model: str = Field(default="llama3.1", description="Target model name.")
    selected_embedding: str = Field(default="nomic-embed-text", description="Target embedding model name.")
    selected_provider: str = Field(default="ollama", description="Active API provider.")
    temperature: float = Field(default=0.0, description="Model generation temperature.")
    max_tokens: int = Field(default=2048, description="Output token limits.")


# =====================================================================
# METADATA & TELEMETRY
# =====================================================================

class TokenUsage(BaseModel):
    """Token consumption data."""
    model_config = ConfigDict(frozen=True)

    prompt_tokens: int = Field(default=0, description="Prompt tokens.")
    completion_tokens: int = Field(default=0, description="Completion tokens.")
    total_tokens: int = Field(default=0, description="Total tokens.")


class NodeExecutionLog(BaseModel):
    """Telemetry trace log details for an individual execution node."""
    model_config = ConfigDict(frozen=True)

    node_name: str = Field(..., description="Target node key name.")
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: float = Field(..., description="Execution duration in milliseconds.")
    input_tokens: int = Field(default=0)
    output_tokens: int = Field(default=0)
    memory_used_bytes: int = Field(default=0, description="Memory size consumed by processing.")
    model_used: Optional[str] = Field(default=None)
    success: bool = Field(..., description="Whether execution was completed without errors.")
    error_message: Optional[str] = Field(default=None)


class RunMetadata(BaseModel):
    """System telemetry logs."""
    model_config = ConfigDict(frozen=True)

    graph_execution_id: UUID = Field(default_factory=uuid4, description="Unique trace identifier.")
    timestamps: Dict[str, datetime] = Field(
        default_factory=lambda: {"initialized": datetime.now(timezone.utc)},
        description="Node entry/exit checkpoints."
    )
    execution_time_ms: Dict[str, float] = Field(default_factory=dict, description="Performance traces.")
    token_usage: Dict[str, TokenUsage] = Field(default_factory=dict, description="Token consumption metrics.")
    node_execution_logs: List[NodeExecutionLog] = Field(default_factory=list, description="Performance trace history across execution graph.")
    debug_information: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic logs.")


# =====================================================================
# CHECKPOINT (LangGraph Resume Linkage)
# =====================================================================

class BrainCheckpoint(BaseModel):
    """Checkpoint metadata representation for resumable StateGraph runs."""
    model_config = ConfigDict(frozen=True)

    checkpoint_id: UUID = Field(default_factory=uuid4, description="Unique checkpoint snapshot identifier.")
    node_name: str = Field(..., description="Orchestration node name where snapshot was generated.")
    state_snapshot_hash: str = Field(..., description="Hash of the state configuration payload.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp.")
    resume_token: str = Field(..., description="Validation token required to resume execution from this checkpoint.")


# =====================================================================
# MAIN ORCHESTRATION STATE (flows through StateGraph)
# =====================================================================

class BrainState(BaseModel):
    """The central state representation for PersonaAI.

    This model serves as the single source of truth flowing through the
    LangGraph StateGraph. Every engine receives this state, performs updates
    via Pydantic's immutable copy, and returns the modified instance.
    """
    model_config = ConfigDict(
        frozen=True,
        validate_assignment=True,
        arbitrary_types_allowed=False,
    )

    # State Versioning
    schema_version: str = Field(default="1.0.0", description="Strictly versioned state contract signature.")

    # Context & Routing (ReadOnly Context + Graph Location Context)
    context: BrainContext = Field(..., description="User configuration and environmental metadata.")
    execution: ExecutionContext = Field(default_factory=ExecutionContext, description="Orchestrator navigation variables.")

    # Engine States
    conversation: ConversationWindow = Field(default_factory=ConversationWindow, description="Active communication history window.")
    memory: MemoryState = Field(default_factory=MemoryState, description="Retrieved long-term and short-term memory traces.")
    knowledge: KnowledgeState = Field(default_factory=KnowledgeState, description="Sub-graph structures matching input entities.")
    communication_intelligence: CommunicationIntelligence = Field(default_factory=CommunicationIntelligence, description="Classified intent details.")
    entities: List[Entity] = Field(default_factory=list, description="Extracted entity collection.")
    tasks: List[Task] = Field(default_factory=list, description="Identified tasks list.")
    planning: PlanningState = Field(default_factory=PlanningState, description="Sequenced plan actions.")
    rag: RAGState = Field(default_factory=RAGState, description="Retrieval query and match traces.")
    tool_calling: ToolState = Field(default_factory=ToolState, description="Tool registry and execution outputs.")
    response: ResponseGeneration = Field(default_factory=ResponseGeneration, description="Compiled prompt values and output targets.")
    learning: LearningState = Field(default_factory=LearningState, description="Learned observations scheduled for commit.")

    # Shared Telemetry & Control Variables
    events: EventState = Field(default_factory=EventState, description="Internal queue of published engine events.")
    decisions: DecisionState = Field(default_factory=DecisionState, description="Traceable engine reasoning metrics.")
    token_budget: TokenBudget = Field(default_factory=TokenBudget, description="Context constraints tracker.")
    model_routing: ModelRouting = Field(default_factory=ModelRouting, description="Model mapping configuration.")
    metadata: RunMetadata = Field(default_factory=RunMetadata, description="Telemetry tracker.")
    checkpoint: Optional[BrainCheckpoint] = Field(default=None, description="Graph checkpoint configuration.")

    # =================================================================
    # STATE MUTATOR HELPERS (For safe immutable copying)
    # =================================================================

    def update(self, **kwargs) -> BrainState:
        """Returns a new copy of the BrainState with fields modified.

        Allows simple partial state updates in a thread-safe, immutable pattern.
        Example:
            state = state.update(response=state.response.model_copy(update={'formatted_response': 'Hello!'}))
        """
        return self.model_copy(update=kwargs)
