"""Priority classification enums."""

from enum import StrEnum


class Priority(StrEnum):
    """Supported priority levels for future intelligence features."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
