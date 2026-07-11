"""Persistent SQLAlchemy models for the AI Brain subsystem."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class TimestampMixin:
    """Common created/updated timestamp fields for brain entities."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class BrainSession(Base, TimestampMixin):
    """An interactive session that groups brain activity for a user."""

    __tablename__ = "brain_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")
    runs: Mapped[list["BrainRun"]] = relationship(
        "BrainRun",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        "Reminder",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    insights: Mapped[list["Insight"]] = relationship(
        "Insight",
        back_populates="session",
        cascade="all, delete-orphan",
    )
    conversation_summaries: Mapped[list["ConversationSummary"]] = relationship(
        "ConversationSummary",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class BrainRun(Base, TimestampMixin):
    """A single execution cycle of the AI brain orchestration logic."""

    __tablename__ = "brain_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    trigger: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    session: Mapped["BrainSession | None"] = relationship(
        "BrainSession", back_populates="runs"
    )
    user: Mapped["User"] = relationship("User")
    actions: Mapped[list["AIAction"]] = relationship(
        "AIAction",
        back_populates="run",
        cascade="all, delete-orphan",
    )
    thoughts: Mapped[list["AIThought"]] = relationship(
        "AIThought",
        back_populates="run",
        cascade="all, delete-orphan",
    )
    retrieval_logs: Mapped[list["RetrievalLog"]] = relationship(
        "RetrievalLog",
        back_populates="run",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="run",
        cascade="all, delete-orphan",
    )


class BrainState(Base, TimestampMixin):
    """A flexible snapshot of brain state for a session or user."""

    __tablename__ = "brain_states"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    state_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    state_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user: Mapped["User"] = relationship("User")


class Memory(Base, TimestampMixin):
    """Long-term memory entry the brain can retrieve later."""

    __tablename__ = "memories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    memory_type: Mapped[str] = mapped_column(
        String(50), default="general", nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(default=None, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")


class Knowledge(Base, TimestampMixin):
    """Structured knowledge stored for retrieval and reasoning."""

    __tablename__ = "knowledge"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    knowledge_type: Mapped[str] = mapped_column(
        String(50), default="fact", nullable=False
    )
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")
    outgoing_relations: Mapped[list["KnowledgeRelation"]] = relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.source_knowledge_id",
        back_populates="source_knowledge",
        cascade="all, delete-orphan",
    )
    incoming_relations: Mapped[list["KnowledgeRelation"]] = relationship(
        "KnowledgeRelation",
        foreign_keys="KnowledgeRelation.target_knowledge_id",
        back_populates="target_knowledge",
        cascade="all, delete-orphan",
    )


class KnowledgeRelation(Base, TimestampMixin):
    """Links between knowledge records."""

    __tablename__ = "knowledge_relations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_knowledge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_knowledge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), default="related_to", nullable=False
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    source_knowledge: Mapped["Knowledge"] = relationship(
        "Knowledge",
        foreign_keys=[source_knowledge_id],
        back_populates="outgoing_relations",
    )
    target_knowledge: Mapped["Knowledge"] = relationship(
        "Knowledge",
        foreign_keys=[target_knowledge_id],
        back_populates="incoming_relations",
    )


class Task(Base, TimestampMixin):
    """A task discovered or generated by the brain."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    priority: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")
    session: Mapped["BrainSession | None"] = relationship(
        "BrainSession", back_populates="tasks"
    )
    run: Mapped["BrainRun | None"] = relationship("BrainRun", back_populates="tasks")


class Reminder(Base, TimestampMixin):
    """A reminder surfaced by the brain for follow-up."""

    __tablename__ = "reminders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    due_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")
    session: Mapped["BrainSession | None"] = relationship(
        "BrainSession", back_populates="reminders"
    )


class Insight(Base, TimestampMixin):
    """A synthesized insight produced from existing memory and context."""

    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    insight_type: Mapped[str] = mapped_column(
        String(50), default="general", nullable=False
    )
    confidence: Mapped[float | None] = mapped_column(default=None, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")
    session: Mapped["BrainSession | None"] = relationship(
        "BrainSession", back_populates="insights"
    )


class Fact(Base, TimestampMixin):
    """A factual observation the brain can reference."""

    __tablename__ = "facts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(default=None, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")


class UserPreference(Base, TimestampMixin):
    """A user preference the brain can use when personalizing behavior."""

    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    preference_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    preference_value: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")


class ConversationSummary(Base, TimestampMixin):
    """A compact summary of a conversation for later retrieval."""

    __tablename__ = "conversation_summaries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    summary_type: Mapped[str] = mapped_column(
        String(50), default="conversation", nullable=False
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    user: Mapped["User"] = relationship("User")
    session: Mapped["BrainSession | None"] = relationship(
        "BrainSession",
        back_populates="conversation_summaries",
    )


class AIAction(Base, TimestampMixin):
    """A concrete action emitted by the brain during a run."""

    __tablename__ = "ai_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)

    run: Mapped["BrainRun"] = relationship("BrainRun", back_populates="actions")


class AIThought(Base, TimestampMixin):
    """A reasoning or planning note captured during a brain run."""

    __tablename__ = "ai_thoughts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    thought_type: Mapped[str] = mapped_column(
        String(50), default="reasoning", nullable=False
    )
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    run: Mapped["BrainRun"] = relationship("BrainRun", back_populates="thoughts")


class RetrievalLog(Base, TimestampMixin):
    """A log of retrieval operations performed by the brain."""

    __tablename__ = "retrieval_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brain_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    results_count: Mapped[int | None] = mapped_column(default=None, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(default=None, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )

    run: Mapped["BrainRun | None"] = relationship(
        "BrainRun", back_populates="retrieval_logs"
    )


class EmbeddingChunk(Base, TimestampMixin):
    """A chunk of text paired with embedding data for semantic retrieval."""

    __tablename__ = "embedding_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_type: Mapped[str] = mapped_column(
        String(50), default="memory", nullable=False
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(JSONB, nullable=True)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata", JSONB, nullable=True
    )
