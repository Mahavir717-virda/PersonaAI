"""Generates rollback instructions to revert completed actions on execution failures."""

from __future__ import annotations

from typing import List
from app.brain.planning.models import Step


class PlanRollbackGenerator:
    """Populates rollback steps to revert changes in case of failure."""

    @staticmethod
    def populate_rollback_steps(steps: List[Step]) -> List[Step]:
        """Maps default rollback/undo descriptions to each step based on its action type."""
        for step in steps:
            title_lower = step.title.lower()
            
            if "create" in title_lower or "add" in title_lower:
                step.rollback_step = f"Delete/Remove: {step.title.replace('Create', '').replace('Add', '').strip()}"
            elif "send" in title_lower:
                step.rollback_step = "Recall or delete draft from sent/outbox folder."
            elif "update" in title_lower:
                step.rollback_step = "Restore previous state value from checkpoint backups."
            elif "delete" in title_lower or "remove" in title_lower:
                step.rollback_step = "Recreate deleted record from backup history logs."
            else:
                # Read-only operations do not need rollbacks
                step.rollback_step = None

        return steps
