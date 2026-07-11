"""Generates alternative backup execution plans for recovery paths."""

from __future__ import annotations

from typing import List
from uuid import uuid4
from app.brain.planning.models import Step, Plan


class PlanFallbackGenerator:
    """Generates alternative plans or backup steps for execution nodes."""

    @staticmethod
    def generate_fallback_plan(original_plan: Plan) -> Plan:
        """Constructs an alternative execution plan with retry configurations or secondary routes."""
        fallback_steps: List[Step] = []

        # Duplicate original steps and append retry/alternative paths
        for original_step in original_plan.steps:
            fallback_steps.append(original_step)

            # If tool requires a network API call, generate a fallback step
            if original_step.tool_required:
                fallback_step = Step(
                    step_id=str(uuid4()),
                    title=f"Fallback: {original_step.title}",
                    description=f"Backup pathway for: {original_step.description}",
                    order=original_step.order + 1,
                    status="pending",
                    dependencies=[original_step.step_id],
                )
                fallback_steps.append(fallback_step)

        # Re-index order sequences
        for idx, step in enumerate(fallback_steps):
            step.order = idx + 1

        fallback_plan = Plan(
            plan_id=str(uuid4()),
            goal=f"Fallback route for: {original_plan.goal}",
            summary=f"Alternative path built for: {original_plan.summary}",
            confidence=max(0.1, original_plan.confidence - 0.2),
            execution_strategy="sequential",
            status="pending",
            steps=fallback_steps
        )
        return fallback_plan
