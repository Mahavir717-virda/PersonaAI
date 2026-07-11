"""Implementation of the PlanningEngine."""

from __future__ import annotations

from typing import List, Dict

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState, PlanningState, PlannedAction
from app.database.session import async_session_factory
from app.brain.planning.repository import PlanRepository
from app.brain.planning.planner import GoalPlanner


class PlanningEngine(BrainEngine):
    """Planning Engine node decomposing goals into structured execution DAGs."""

    def __init__(self, planner: GoalPlanner | None = None) -> None:
        self.planner = planner or GoalPlanner()

    @property
    def name(self) -> str:
        return "planning"

    async def execute(self, state: BrainState) -> BrainState:
        incoming = state.conversation.incoming_message
        if not incoming or not incoming.content:
            return state

        goal_text = incoming.content
        user_id = state.context.user_profile.user_id

        # Compile any active task contexts to enrich prompt inputs
        task_contexts = "; ".join([t.title for t in state.tasks])
        context_details = f"Active Tasks: {task_contexts}" if task_contexts else ""

        async with async_session_factory() as session:
            repository = PlanRepository(session)

            # 1. Decompose goal into plan DAG
            plan = await self.planner.generate_plan(
                goal=goal_text,
                context_details=context_details,
                model=state.model_routing.selected_model,
            )

            # 2. Persist plan and steps to database
            await repository.save_plan(user_id, plan)

            # 3. Convert steps into Pydantic PlannedAction objects to update state.planning
            actions: List[PlannedAction] = []
            order_ids: List[str] = []
            deps_map: Dict[str, List[str]] = {}

            for step in plan.steps:
                actions.append(PlannedAction(
                    action_id=step.step_id,
                    name=step.title,
                    parameters={
                        "description": step.description,
                        "tool_required": step.tool_required,
                        "memory_required": step.memory_required,
                        "knowledge_required": step.knowledge_required,
                        "rag_required": step.rag_required,
                        "automation_required": step.automation_required,
                        "approval_required": step.approval_required,
                        "parallel_group": step.parallel_group,
                        "rollback_step": step.rollback_step,
                    },
                    description=step.description
                ))
                order_ids.append(step.step_id)
                deps_map[step.step_id] = step.dependencies

            new_planning_state = PlanningState(
                planned_actions=actions,
                execution_order=order_ids,
                dependencies=deps_map,
                next_best_action=actions[0] if actions else None,
                confidence=plan.confidence,
            )

            return state.update(planning=new_planning_state)

    async def validate(self, state: BrainState) -> bool:
        return state.context.user_profile.user_id is not None

    async def rollback(self, state: BrainState) -> BrainState:
        return state
