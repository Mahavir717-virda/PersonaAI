"""Database models for the communication and connector domains."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, DateTime, Boolean, Enum as SQLEnum, Text, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums.platform import Platform
from app.enums.connector_state import ConnectorState
from app.enums.communication_status import CommunicationStatus


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps."""

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



class Connector(Base, TimestampMixin):
    """Configuration and credentials for third-party service connections."""

    __tablename__ = "connectors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[Platform] = mapped_column(SQLEnum(Platform), nullable=False)
    state: Mapped[ConnectorState] = mapped_column(
        SQLEnum(ConnectorState), default=ConnectorState.DISCONNECTED, nullable=False
    )
    settings: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    checkpoints: Mapped[list["SyncCheckpoint"]] = relationship(
        "SyncCheckpoint", back_populates="connector", cascade="all, delete-orphan"
    )
    histories: Mapped[list["SyncHistory"]] = relationship(
        "SyncHistory", back_populates="connector", cascade="all, delete-orphan"
    )
    communications: Mapped[list["Communication"]] = relationship(
        "Communication", back_populates="connector", cascade="all, delete-orphan"
    )


class SyncCheckpoint(Base):
    """Synchronization cursor checkpoint per connector/user."""

    __tablename__ = "sync_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    connector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connectors.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    cursor: Mapped[str | None] = mapped_column(String(512), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    connector: Mapped["Connector"] = relationship("Connector", back_populates="checkpoints")


class SyncHistory(Base):
    """Logs detailing sync durations, counts, and errors."""

    __tablename__ = "sync_histories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    connector_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connectors.id", ondelete="CASCADE"), nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    messages_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attachments_imported: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False) # running, success, failed
    duration: Mapped[float | None] = mapped_column(Float, nullable=True)
    error: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    failed_ids: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)

    # Relationships
    connector: Mapped["Connector"] = relationship("Connector", back_populates="histories")


class Conversation(Base):
    """Tracks message threads across external platforms."""

    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    platform: Mapped[Platform] = mapped_column(SQLEnum(Platform), nullable=False)
    platform_conversation_id: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    communications: Mapped[list["Communication"]] = relationship(
        "Communication", back_populates="conversation"
    )


class Communication(Base):
    """Normalized communication record (emails, chats, etc.)."""

    __tablename__ = "communications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    connector_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("connectors.id", ondelete="SET NULL"), nullable=True
    )
    platform: Mapped[Platform] = mapped_column(SQLEnum(Platform), nullable=False)
    platform_message_id: Mapped[str] = mapped_column(
        String(255), index=True, nullable=False
    )
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True
    )
    subject: Mapped[str | None] = mapped_column(String(512), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    html_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CommunicationStatus] = mapped_column(
        SQLEnum(CommunicationStatus), default=CommunicationStatus.NEW, nullable=False
    )
    importance: Mapped[str] = mapped_column(String(50), default="medium", nullable=False) # low, medium, high
    metadata_fields: Mapped[dict | None] = mapped_column(JSONB, name="metadata", nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    connector: Mapped["Connector"] = relationship("Connector", back_populates="communications")
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="communications")
    participants: Mapped[list["Participant"]] = relationship(
        "Participant", back_populates="communication", cascade="all, delete-orphan"
    )
    attachments: Mapped[list["Attachment"]] = relationship(
        "Attachment", back_populates="communication", cascade="all, delete-orphan"
    )


class Participant(Base):
    """Sender, recipient, cc, bcc mapping for messages."""

    __tablename__ = "participants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    communication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("communications.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False) # email, phone, Slack ID
    type: Mapped[str] = mapped_column(String(50), nullable=False) # sender, recipient, cc, bcc

    # Relationships
    communication: Mapped["Communication"] = relationship("Communication", back_populates="participants")


class Attachment(Base):
    """File attachments linked to message communications."""

    __tablename__ = "attachments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    communication_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("communications.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    communication: Mapped["Communication"] = relationship("Communication", back_populates="attachments")
