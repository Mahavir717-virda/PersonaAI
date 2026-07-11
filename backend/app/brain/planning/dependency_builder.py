"""Builds dependency sequences and registers step dependencies."""

from __future__ import annotations

from typing import List
from app.brain.planning.models import Step


class DependencyBuilder:
    """Configures step dependencies to ensure proper topological sorting and execution sequence."""

    @staticmethod
    def resolve_dependencies(steps: List[Step]) -> List[Step]:
        """Resolves raw dependency names and maps them to valid step sequences."""
        title_map = {step.title.lower().strip(): step.step_id for step in steps}

        for step in steps:
            resolved_ids = []
            for dep in step.dependencies:
                dep_clean = dep.lower().strip()
                # If dependency title matches another step's title, link using its step_id
                if dep_clean in title_map:
                    resolved_ids.append(title_map[dep_clean])
                else:
                    # Keep raw title if not matched directly
                    resolved_ids.append(dep)
            step.dependencies = resolved_ids

        return steps
