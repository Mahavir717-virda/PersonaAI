"""Event definitions for background hooks and event loops."""

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ConnectorConnected(BaseModel):
    """Triggered when a third-party platform finishes authentication successfully."""

    connector_id: uuid.UUID
    user_id: uuid.UUID
    platform: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConnectorDisconnected(BaseModel):
    """Triggered when a third-party platform integration is deleted."""

    connector_id: uuid.UUID
    user_id: uuid.UUID
    platform: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SyncStarted(BaseModel):
    """Triggered when a sync pass loop initializes."""

    connector_id: uuid.UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SyncCompleted(BaseModel):
    """Triggered when a sync pass loop completes."""

    connector_id: uuid.UUID
    messages_imported: int
    attachments_imported: int
    duration_seconds: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class MessageImported(BaseModel):
    """Triggered when a normalized communication is written to the database."""

    message_id: uuid.UUID
    platform_message_id: str
    platform: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AttachmentImported(BaseModel):
    """Triggered when a file attachment is successfully imported."""

    attachment_id: uuid.UUID
    communication_id: uuid.UUID
    name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
