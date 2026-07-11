"""Urgency classification helper for Communication Intelligence."""

from __future__ import annotations


class UrgencyDetector:
    """Detects and standardizes urgency levels."""

    VALID_URGENCIES = {"low", "medium", "high"}

    @classmethod
    def clean_urgency(cls, urgency: str | None) -> str:
        """Standardizes raw urgency level string."""
        if not urgency:
            return "low"
        val = urgency.strip().lower()
        return val if val in cls.VALID_URGENCIES else "low"
