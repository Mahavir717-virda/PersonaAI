"""Estimates computational tokens and financial dollar costs for plans."""

from __future__ import annotations

from typing import List
from app.brain.planning.models import Step


class CostEstimator:
    """Predicts token consumption and API pricing dollar estimates for plan actions."""

    # Default cost per 1k tokens: $0.0015
    TOKEN_PRICE_MULTIPLIER = 0.0015 / 1000.0

    @classmethod
    def estimate_plan_cost(cls, steps: List[Step]) -> float:
        """Sums estimated tokens and computes total dollar cost."""
        total_tokens = 0
        for step in steps:
            # Assign a baseline if estimated tokens is missing
            tokens = step.estimated_tokens if step.estimated_tokens > 0 else 1000
            step.estimated_tokens = tokens
            total_tokens += tokens

        return float(total_tokens * cls.TOKEN_PRICE_MULTIPLIER)
