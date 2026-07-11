"""Calculates and updates confidence levels for Knowledge Graph components."""

from __future__ import annotations


class KnowledgeConfidence:
    """Manages confidence score updates based on repetition, confirmation, or contradiction."""

    @staticmethod
    def calculate_new_confidence(
        current_confidence: float,
        extraction_score: float = 1.0,
        feedback_type: str | None = None
    ) -> float:
        """Applies updates to the confidence score based on feedback type (confirm, contradict)."""
        if feedback_type == "confirm":
            # Asymptotic boost towards 1.0
            return min(1.0, current_confidence + (1.0 - current_confidence) * 0.25)
        
        if feedback_type == "contradict":
            # Significant drop on contradiction
            return max(0.0, current_confidence - 0.4)

        # Baseline confidence recalculation combining current value and extraction score
        return min(1.0, max(0.0, (current_confidence * 0.7) + (extraction_score * 0.3)))
