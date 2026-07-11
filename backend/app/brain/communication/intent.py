"""Intent classification helper for Communication Intelligence."""

from __future__ import annotations


class IntentDetector:
    """Detects and standardizes user communication intents."""

    VALID_INTENTS = {"request", "inform", "greeting", "question", "apology", "complaint", "unknown"}

    @classmethod
    def clean_intent(cls, intent: str | None) -> str:
        """Standardizes raw intent string to valid set."""
        if not intent:
            return "unknown"
        val = intent.strip().lower()
        return val if val in cls.VALID_INTENTS else "unknown"
