"""Tone classification helper for Communication Intelligence."""

from __future__ import annotations


class ToneDetector:
    """Detects and standardizes user communication tones."""

    VALID_TONES = {"professional", "casual", "urgent", "polite", "neutral"}

    @classmethod
    def clean_tone(cls, tone: str | None) -> str:
        """Standardizes raw tone string."""
        if not tone:
            return "neutral"
        val = tone.strip().lower()
        return val if val in cls.VALID_TONES else "neutral"
