"""Processing status enums."""

from enum import StrEnum


class ProcessingStatus(StrEnum):
    """Supported processing lifecycle states."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
