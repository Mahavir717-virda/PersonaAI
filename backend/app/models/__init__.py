"""ORM model package for database tables."""

from importlib import import_module

from app.models.user import User, UserProfile, UserSettings
from app.models.refresh_token import RefreshToken
from app.models.session import UserSession
from app.models.audit_log import AuditLog
from app.models.connector_account import ConnectorAccount
from app.models.communication_account import CommunicationAccount
from app.models.communication import (
    Connector,
    SyncCheckpoint,
    SyncHistory,
    Conversation,
    Communication,
    Participant,
    Attachment,
)

_BRAIN_EXPORTS = {
    "AIAction": "app.brain.models",
    "AIThought": "app.brain.models",
    "BrainRun": "app.brain.models",
    "BrainSession": "app.brain.models",
    "BrainState": "app.brain.models",
    "ConversationSummary": "app.brain.models",
    "EmbeddingChunk": "app.brain.models",
    "Fact": "app.brain.models",
    "Insight": "app.brain.models",
    "Knowledge": "app.brain.models",
    "KnowledgeRelation": "app.brain.models",
    "Memory": "app.brain.models",
    "Reminder": "app.brain.models",
    "RetrievalLog": "app.brain.models",
    "Task": "app.brain.models",
    "UserPreference": "app.brain.models",
}


def __getattr__(name: str):
    if name in _BRAIN_EXPORTS:
        module = import_module(_BRAIN_EXPORTS[name])
        return getattr(module, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "User",
    "UserProfile",
    "UserSettings",
    "RefreshToken",
    "UserSession",
    "AuditLog",
    "ConnectorAccount",
    "CommunicationAccount",
    "Connector",
    "SyncCheckpoint",
    "SyncHistory",
    "Conversation",
    "Communication",
    "Participant",
    "Attachment",
    *sorted(_BRAIN_EXPORTS),
]
