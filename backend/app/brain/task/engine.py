"""Implementation of the TaskEngine."""

from __future__ import annotations

from typing import List

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState, Task, TaskPriority, TaskStatus
from app.database.session import async_session_factory
from app.brain.task.repository import TaskRepository
from app.brain.task.extractor import TaskExtractor
from app.brain.task.deadline import DeadlineResolver
from app.brain.task.dependency import TaskDependencyBuilder


class TaskEngine(BrainEngine):
    """Task Extraction Engine parsing commitments, scheduling deadlines, and managing dependencies."""

    def __init__(self, extractor: TaskExtractor | None = None) -> None:
        self.extractor = extractor or TaskExtractor()

    @property
    def name(self) -> str:
        return "task"

    async def execute(self, state: BrainState) -> BrainState:
        # 1. Skip activation if Communication Intelligence says there are no tasks
        if not state.communication_intelligence.contains_task:
            return state

        incoming = state.conversation.incoming_message
        if not incoming or not incoming.content:
            return state

        user_id = state.context.user_profile.user_id

        async with async_session_factory() as session:
            repository = TaskRepository(session)

            # 2. Extract raw tasks
            raw_tasks = await self.extractor.extract_tasks(
                text=incoming.content,
                model=state.model_routing.selected_model,
            )

            if not raw_tasks:
                return state

            # 3. Resolve dependencies
            sequenced_tasks = TaskDependencyBuilder.build_dependencies(raw_tasks)

            # 4. Save extracted tasks into database
            for t in sequenced_tasks:
                title = t.get("title", "Action Item")
                owner = t.get("owner", "user")
                
                # Resolve relative deadline string to datetime
                due_dt = None
                raw_dl = t.get("deadline")
                if raw_dl:
                    due_dt = DeadlineResolver.resolve_relative_deadline(raw_dl)

                priority_str = t.get("priority", "medium").lower()
                status_str = t.get("status", "pending").lower()

                await repository.create_task(
                    user_id=user_id,
                    title=title,
                    description=f"Owner: {owner}",
                    status=status_str,
                    priority=priority_str,
                    due_at=due_dt,
                    metadata={"depends_on": t.get("resolved_dependencies", [])},
                )

            # 5. Load all user tasks to populate state.tasks
            db_tasks = await repository.get_tasks_by_user(user_id)
            updated_tasks: List[Task] = []
            for dbt in db_tasks:
                try:
                    pri = TaskPriority(dbt.priority.lower())
                except ValueError:
                    pri = TaskPriority.MEDIUM

                try:
                    sta = TaskStatus(dbt.status.lower())
                except ValueError:
                    sta = TaskStatus.PENDING

                updated_tasks.append(Task(
                    task_id=dbt.id,
                    title=dbt.title,
                    description=dbt.description,
                    deadline=dbt.due_at,
                    priority=pri,
                    status=sta,
                    owner="user",
                ))

            return state.update(tasks=updated_tasks)

    async def validate(self, state: BrainState) -> bool:
        return state.context.user_profile.user_id is not None

    async def rollback(self, state: BrainState) -> BrainState:
        return state
