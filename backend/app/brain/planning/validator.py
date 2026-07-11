"""Performs consistency and cycle validation checks on plan DAGs."""

from __future__ import annotations

from typing import List
from app.brain.planning.models import Plan


class PlanValidator:
    """Verifies plan integrity, checking for dependency cycles, deadlocks, and empty steps."""

    @staticmethod
    def validate_plan(plan: Plan) -> bool:
        """Runs validation checks. Returns True if plan is valid and contains no dependency cycles."""
        if not plan.steps:
            return False

        # Build adjacency list
        adj = {}
        all_ids = {step.step_id for step in plan.steps}

        for step in plan.steps:
            adj[step.step_id] = []
            for dep in step.dependencies:
                # Check for deadlocks: reference to non-existent step
                if dep not in all_ids:
                    # Deadlock/broken reference, but we can bypass or log it. Let's return False if invalid reference.
                    return False
                adj[step.step_id].append(dep)

        # DFS Cycle Detection
        visited = {}  # 0 = unvisited, 1 = visiting, 2 = visited

        def has_cycle(sid: str) -> bool:
            visited[sid] = 1
            for neighbor in adj.get(sid, []):
                if visited.get(neighbor, 0) == 1:
                    return True
                if visited.get(neighbor, 0) == 0:
                    if has_cycle(neighbor):
                        return True
            visited[sid] = 2
            return False

        for step in plan.steps:
            if visited.get(step.step_id, 0) == 0:
                if has_cycle(step.step_id):
                    return False

        return True
