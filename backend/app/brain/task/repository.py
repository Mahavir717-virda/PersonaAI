"""Database repository for Task entities in PostgreSQL."""

from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.brain.models.brain_models import Task


class TaskRepository(BaseRepository[Task]):
    """SQLAlchemy Repository for managing Task records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Task)

    async def create_task(
        self,
        user_id: UUID,
        title: str,
        description: str | None = None,
        status: str = "pending",
        priority: str = "medium",
        due_at: datetime | None = None,
        metadata: Dict[str, Any] | None = None,
    ) -> Task:
        """Saves a new task discovery to the database."""
        task = Task(
            id=uuid4(),
            user_id=user_id,
            title=title,
            description=description,
            status=status,
            priority=priority,
            due_at=due_at,
            metadata_=metadata or {},
        )
        self.session.add(task)
        await self.session.commit()
        return task

    async def get_tasks_by_user(self, user_id: UUID) -> List[Task]:
        """Loads all active tasks for a user."""
        stmt = select(Task).where(Task.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
