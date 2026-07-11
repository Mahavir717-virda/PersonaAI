"""Confidence calculations for Communication Intelligence."""

from __future__ import annotations


class ConfidenceCalculator:
    """Predicts confidence scaling for communication properties."""

    @staticmethod
    def calculate_confidence(raw_score: float | None) -> float:
        """Returns normalized float score (0.0 to 1.0) with fallbacks."""
        if raw_score is None:
            return 0.8
        return max(0.0, min(1.0, float(raw_score)))
