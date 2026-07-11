"""Stub implementation of the PlanningEngine."""

from __future__ import annotations

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState


class PlanningEngine(BrainEngine):
    """Planning Engine stub."""

    @property
    def name(self) -> str:
        return "planning"

    async def execute(self, state: BrainState) -> BrainState:
        return state

    async def validate(self, state: BrainState) -> bool:
        return True

    async def rollback(self, state: BrainState) -> BrainState:
        return state
