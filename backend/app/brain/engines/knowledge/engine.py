"""Stub implementation of the KnowledgeEngine."""

from __future__ import annotations

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState


class KnowledgeEngine(BrainEngine):
    """Knowledge Engine stub."""

    @property
    def name(self) -> str:
        return "knowledge"

    async def execute(self, state: BrainState) -> BrainState:
        return state

    async def validate(self, state: BrainState) -> bool:
        return True

    async def rollback(self, state: BrainState) -> BrainState:
        return state
