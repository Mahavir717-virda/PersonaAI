"""Resolves task sequences and sequential dependency structures."""

from __future__ import annotations

from typing import Any, Dict, List
from uuid import UUID


class TaskDependencyBuilder:
    """Structures extracted tasks into sequenced graphs representing dependencies."""

    @staticmethod
    def build_dependencies(tasks_payload: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Maps depends_on title strings to sequential structures."""
        # Map titles to index positions or dependency structures
        # In a flat Pydantic model state, we can represent dependencies as target metadata UUID lists.
        # This helper links each task record to its prerequisite tasks.
        title_to_task = {t["title"].lower(): t for t in tasks_payload}

        for task in tasks_payload:
            deps = task.get("depends_on", [])
            dependency_ids = []
            
            for dep_title in deps:
                matched_task = title_to_task.get(dep_title.lower())
                if matched_task:
                    # Stored in the task record metadata to link them
                    dependency_ids.append(matched_task["title"])

            task["resolved_dependencies"] = dependency_ids

        return tasks_payload
