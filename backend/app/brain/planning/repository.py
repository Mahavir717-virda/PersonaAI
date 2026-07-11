"""Database repository layer for Plan and Plan Step persistence in PostgreSQL."""

from __future__ import annotations

from uuid import UUID, uuid4
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.base import BaseRepository
from app.brain.planning.models import PlanRecord, PlanStepRecord, Plan, Step


class PlanRepository(BaseRepository[PlanRecord]):
    """SQLAlchemy Repository for managing Plan and Step database records."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PlanRecord)

    async def save_plan(self, user_id: UUID, plan: Plan) -> PlanRecord:
        """Saves a plan and its DAG steps to the database."""
        plan_uuid = UUID(plan.plan_id)
        
        # 1. Create PlanRecord
        plan_record = PlanRecord(
            id=plan_uuid,
            user_id=user_id,
            goal=plan.goal,
            summary=plan.summary,
            confidence=plan.confidence,
            estimated_cost=plan.estimated_cost,
            estimated_duration=plan.estimated_duration,
            execution_strategy=plan.execution_strategy,
            status=plan.status,
            metadata_={},
        )
        self.session.add(plan_record)

        # 2. Create PlanStepRecords
        for step in plan.steps:
            step_record = PlanStepRecord(
                id=UUID(step.step_id),
                plan_id=plan_uuid,
                title=step.title,
                description=step.description,
                step_order=step.order,
                status=step.status,
                tool_required=step.tool_required,
                memory_required=step.memory_required,
                knowledge_required=step.knowledge_required,
                rag_required=step.rag_required,
                automation_required=step.automation_required,
                approval_required=step.approval_required,
                estimated_duration=step.estimated_duration,
                estimated_tokens=step.estimated_tokens,
                retry_count=step.retry_count,
                dependencies=step.dependencies,
                parallel_group=step.parallel_group,
                rollback_step=step.rollback_step,
            )
            self.session.add(step_record)

        await self.session.commit()
        return plan_record

    async def get_plan_with_steps(self, plan_id: UUID) -> Optional[PlanRecord]:
        """Loads a plan record fully joined with its steps."""
        stmt = (
            select(PlanRecord)
            .options(selectinload(PlanRecord.steps))
            .where(PlanRecord.id == plan_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_plans_by_user(self, user_id: UUID) -> List[PlanRecord]:
        """Loads all plans generated for a specific user."""
        stmt = (
            select(PlanRecord)
            .options(selectinload(PlanRecord.steps))
            .where(PlanRecord.user_id == user_id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
