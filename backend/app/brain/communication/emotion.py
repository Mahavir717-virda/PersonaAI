"""Emotion classification helper for Communication Intelligence."""

from __future__ import annotations


class EmotionDetector:
    """Detects and standardizes user emotional states."""

    VALID_EMOTIONS = {"neutral", "happy", "frustrated", "anxious", "grateful"}

    @classmethod
    def clean_emotion(cls, emotion: str | None) -> str:
        """Standardizes raw emotion string."""
        if not emotion:
            return "neutral"
        val = emotion.strip().lower()
        return val if val in cls.VALID_EMOTIONS else "neutral"
