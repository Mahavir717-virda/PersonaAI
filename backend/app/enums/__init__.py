"""Shared application enums."""

from app.enums.platform import Platform
from app.enums.priority import Priority
from app.enums.status import ProcessingStatus
from app.enums.role import UserRole
from app.enums.account_status import AccountStatus
from app.enums.connector_state import ConnectorState
from app.enums.communication_status import CommunicationStatus

__all__ = [
    "Platform",
    "Priority",
    "ProcessingStatus",
    "UserRole",
    "AccountStatus",
    "ConnectorState",
    "CommunicationStatus",
]


