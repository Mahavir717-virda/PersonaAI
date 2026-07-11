"""Orchestrator class for decomposing goals and structuring executable plan DAGs."""

from __future__ import annotations

import json
import httpx
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.brain.planning.models import Plan, Step
from app.brain.planning.prompts import PLANNING_PROMPT
from app.brain.planning.dependency_builder import DependencyBuilder
from app.brain.planning.parallelizer import PlanParallelizer
from app.brain.planning.cost_estimator import CostEstimator
from app.brain.planning.duration_estimator import DurationEstimator
from app.brain.planning.rollback import PlanRollbackGenerator
from app.brain.planning.validator import PlanValidator
from app.brain.planning.workflow import PlanWorkflow


class GoalPlanner:
    """Core goal decomposition engine that transforms natural language goals into validated plan DAGs."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def generate_plan(self, goal: str, context_details: str = "", model: str | None = None) -> Plan:
        """Calls local LLMs to generate plan steps, returning a fully validated Plan DAG."""
        model_name = model or self.default_model
        prompt = PLANNING_PROMPT.format(goal=goal, context=context_details)

        raw_plan = None
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                    },
                    timeout=45.0,
                )
                response.raise_for_status()
                data = json.loads(response.json()["response"])
                
                # Parse steps list
                steps = []
                for idx, s in enumerate(data.get("steps", [])):
                    steps.append(Step(
                        step_id=str(uuid4()),
                        title=s.get("title", "Action"),
                        description=s.get("description", ""),
                        order=idx + 1,
                        tool_required=s.get("tool_required"),
                        memory_required=bool(s.get("memory_required", False)),
                        knowledge_required=bool(s.get("knowledge_required", False)),
                        rag_required=bool(s.get("rag_required", False)),
                        automation_required=bool(s.get("automation_required", False)),
                        approval_required=bool(s.get("approval_required", False)),
                        estimated_duration=float(s.get("estimated_duration", 5.0)),
                        estimated_tokens=int(s.get("estimated_tokens", 1000)),
                        dependencies=s.get("dependencies", []),
                    ))

                raw_plan = Plan(
                    plan_id=str(uuid4()),
                    goal=data.get("goal", goal),
                    summary=data.get("summary", "Custom LLM plan."),
                    confidence=float(data.get("confidence", 0.9)),
                    execution_strategy=data.get("execution_strategy", "sequential"),
                    status="pending",
                    steps=steps
                )
            except Exception:
                pass

        if not raw_plan:
            # Fallback heuristic planner when LLM is offline
            raw_plan = self._generate_fallback_heuristic_plan(goal)

        # Apply graph transformations
        # 1. Resolve raw title dependencies into structural step_ids
        raw_plan.steps = DependencyBuilder.resolve_dependencies(raw_plan.steps)

        # 2. Topologically sort steps based on dependency sequence
        raw_plan.steps = PlanWorkflow.topologically_sort_steps(raw_plan)

        # 3. Identify parallel execution groups
        raw_plan.steps = PlanParallelizer.identify_parallel_groups(raw_plan.steps)

        # 4. Estimate final cost metrics
        raw_plan.estimated_cost = CostEstimator.estimate_plan_cost(raw_plan.steps)

        # 5. Estimate final duration metrics
        raw_plan.estimated_duration = DurationEstimator.estimate_plan_duration(raw_plan.steps)

        # 6. Populate undo rollback steps
        raw_plan.steps = PlanRollbackGenerator.populate_rollback_steps(raw_plan.steps)

        # 7. Plan validation integrity check
        is_valid = PlanValidator.validate_plan(raw_plan)
        if not is_valid:
            # Revert to a clean sequential fallback list to ensure cycle-free run
            clean_steps = []
            for idx, step in enumerate(raw_plan.steps):
                clean_steps.append(step.model_copy(update={
                    "dependencies": [clean_steps[-1].step_id] if clean_steps else [],
                    "parallel_group": None
                }))
            raw_plan.steps = clean_steps

        return raw_plan

    def _generate_fallback_heuristic_plan(self, goal: str) -> Plan:
        """Builds a basic sequential execution step list based on task keywords."""
        goal_lower = goal.lower()
        steps = []

        if "meeting" in goal_lower or "schedule" in goal_lower or "calendar" in goal_lower or "invitation" in goal_lower or "slot" in goal_lower:
            steps = [
                Step(title="Check Calendar Availability", description="Lookup user slots", order=1, tool_required="calendar"),
                Step(title="Create Invitation", description="Propose slot to invitee", order=2, tool_required="calendar", dependencies=["Check Calendar Availability"]),
                Step(title="Send Email", description="Send invitation confirmation", order=3, tool_required="gmail", dependencies=["Create Invitation"]),
            ]
        elif "email" in goal_lower or "reply" in goal_lower or "send" in goal_lower:
            steps = [
                Step(title="Read Inbox Thread", description="Load details from email", order=1, tool_required="gmail"),
                Step(title="Generate Response Draft", description="Draft email using RAG", order=2, rag_required=True, dependencies=["Read Inbox Thread"]),
                Step(title="Send Email Response", description="Post draft to Gmail", order=3, tool_required="gmail", dependencies=["Generate Response Draft"]),
            ]
        else:
            steps = [
                Step(title="Analyze User Request", description="Decompose intent details", order=1),
                Step(title="Execute Action", description="Process execution", order=2, dependencies=["Analyze User Request"]),
            ]

        return Plan(
            plan_id=str(uuid4()),
            goal=goal,
            summary="Heuristics fallback plan.",
            confidence=0.5,
            execution_strategy="sequential",
            status="pending",
            steps=steps
        )
