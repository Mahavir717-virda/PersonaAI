"""Priority classification helper for Communication Intelligence."""

from __future__ import annotations


class PriorityDetector:
    """Detects and standardizes priority levels."""

    VALID_PRIORITIES = {"low", "medium", "high"}

    @classmethod
    def clean_priority(cls, priority: str | None) -> str:
        """Standardizes raw priority level string."""
        if not priority:
            return "medium"
        val = priority.strip().lower()
        return val if val in cls.VALID_PRIORITIES else "medium"
