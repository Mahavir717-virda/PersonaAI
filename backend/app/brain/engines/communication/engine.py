"""Stub implementation of the CommunicationEngine."""

from __future__ import annotations

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState


class CommunicationEngine(BrainEngine):
    """Communication Engine stub."""

    @property
    def name(self) -> str:
        return "communication"

    async def execute(self, state: BrainState) -> BrainState:
        return state

    async def validate(self, state: BrainState) -> bool:
        return True

    async def rollback(self, state: BrainState) -> BrainState:
        return state
