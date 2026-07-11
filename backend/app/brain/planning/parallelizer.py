"""Finds independent steps that can be run concurrently."""

from __future__ import annotations

from typing import List
from app.brain.planning.models import Step


class PlanParallelizer:
    """Groups independent steps into parallel execution lanes."""

    @staticmethod
    def identify_parallel_groups(steps: List[Step]) -> List[Step]:
        """Groups independent steps sharing no common dependencies into parallel execution lanes."""
        # Clean existing groups
        for step in steps:
            step.parallel_group = None

        # Simple grouping: steps at the same "level" of the dependency tree
        # Level 0: no dependencies
        # Level 1: depends on Level 0, etc.
        resolved = {}
        for step in steps:
            resolved[step.step_id] = step

        # Calculate levels
        levels = {}
        
        def get_level(sid: str) -> int:
            if sid in levels:
                return levels[sid]
            step = resolved.get(sid)
            if not step or not step.dependencies:
                levels[sid] = 0
                return 0
            
            # Level is max of dependencies + 1
            max_dep_level = 0
            for dep in step.dependencies:
                max_dep_level = max(max_dep_level, get_level(dep))
            levels[sid] = max_dep_level + 1
            return levels[sid]

        for step in steps:
            get_level(step.step_id)

        # Group steps by level if there are multiple steps at the same level
        level_groups = {}
        for sid, lvl in levels.items():
            level_groups.setdefault(lvl, []).append(sid)

        for lvl, sids in level_groups.items():
            if len(sids) > 1:
                # Assign a parallel group name
                group_name = f"parallel-group-level-{lvl}"
                for sid in sids:
                    resolved[sid].parallel_group = group_name

        return steps
