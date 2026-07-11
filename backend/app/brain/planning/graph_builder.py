"""Compiles plan lists into directed acyclic graph (DAG) step records."""

from __future__ import annotations

from typing import List, Dict, Set
from app.brain.planning.models import Plan, Step


class PlanGraphBuilder:
    """Builds DAG execution structures, resolving sequential, parallel, and conditional execution lanes."""

    @staticmethod
    def build_dag_adjacency(plan: Plan) -> Dict[str, List[str]]:
        """Compiles step relationships into a forward-directed DAG adjacency list."""
        adj = {}
        for step in plan.steps:
            adj[step.step_id] = []

        # Map dependencies (which are list of prerequisite step IDs) to forward edges
        for step in plan.steps:
            for dep in step.dependencies:
                if dep in adj:
                    adj[dep].append(step.step_id)

        return adj

    @staticmethod
    def get_roots(plan: Plan) -> List[str]:
        """Finds all root steps (steps with no dependencies) that can execute immediately."""
        roots = []
        for step in plan.steps:
            if not step.dependencies:
                roots.append(step.step_id)
        return roots
