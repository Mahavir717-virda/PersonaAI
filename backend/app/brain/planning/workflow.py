"""Topologically sorts and orders execution step sequences."""

from __future__ import annotations

from collections import deque
from typing import List
from app.brain.planning.models import Plan, Step


class PlanWorkflow:
    """Manages topological ordering and sequencing for step execution flows."""

    @staticmethod
    def topologically_sort_steps(plan: Plan) -> List[Step]:
        """Performs Kahn's topological sort on plan steps to resolve correct sequence orders."""
        steps = plan.steps
        resolved = {step.step_id: step for step in steps}
        
        # Calculate in-degrees
        in_degree = {step.step_id: 0 for step in steps}
        adj = {step.step_id: [] for step in steps}

        for step in steps:
            for dep in step.dependencies:
                if dep in in_degree:
                    adj[dep].append(step.step_id)
                    in_degree[step.step_id] += 1

        # Queue root nodes
        queue = deque([sid for sid, deg in in_degree.items() if deg == 0])
        sorted_ids = []

        while queue:
            curr = queue.popleft()
            sorted_ids.append(curr)
            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        # Re-order based on sorted IDs
        sorted_steps = []
        for idx, sid in enumerate(sorted_ids):
            step = resolved[sid]
            # Mutate order sequence to be 1-indexed
            new_step = step.model_copy(update={"order": idx + 1})
            sorted_steps.append(new_step)

        # Fallback to original list if cycle detected (len mismatch) to prevent losing data
        if len(sorted_steps) != len(steps):
            return steps

        return sorted_steps
