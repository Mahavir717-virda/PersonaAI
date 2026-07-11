"""Estimates execution time duration for sequential and parallel plan DAGs."""

from __future__ import annotations

from typing import List
from app.brain.planning.models import Step


class DurationEstimator:
    """Predicts timeline execution durations, accounting for parallel group overlapping."""

    @classmethod
    def estimate_plan_duration(cls, steps: List[Step]) -> float:
        """Sums durations of sequential steps while taking the max duration for parallel groups."""
        sequential_duration = 0.0
        parallel_group_durations: dict[str, List[float]] = {}

        for step in steps:
            # Assign baseline default duration of 5 seconds if missing/zero
            dur = step.estimated_duration if step.estimated_duration > 0 else 5.0
            step.estimated_duration = dur

            if step.parallel_group:
                parallel_group_durations.setdefault(step.parallel_group, []).append(dur)
            else:
                sequential_duration += dur

        # Add maximum duration from each parallel lane group
        for group, durs in parallel_group_durations.items():
            if durs:
                sequential_duration += max(durs)

        return float(sequential_duration)
