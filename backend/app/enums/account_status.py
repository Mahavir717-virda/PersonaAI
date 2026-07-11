"""Account status enums."""

from enum import StrEnum


class AccountStatus(StrEnum):
    """SaaS account status states."""

    ACTIVE = "active"
    PENDING = "pending"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"
    DELETED = "deleted"
