"""Abstract Base Class defining the contract for all PersonaAI Brain Engines."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.brain.schemas.state import BrainState


class BrainEngine(ABC):
    """The foundational contract that every PersonaAI engine must implement.

    Guarantees consistent naming, validation, execution, and rollback strategies
    across all nodes flowing through the LangGraph StateGraph orchestrator.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """The distinct identifying name of the engine.

        This matches the corresponding orchestrator node name.
        """
        pass

    @abstractmethod
    async def execute(self, state: BrainState) -> BrainState:
        """Executes the core logical processing for the engine.

        Receives the current state, performs mutations via Pydantic model copies,
        and returns the updated state.
        """
        pass

    @abstractmethod
    async def validate(self, state: BrainState) -> bool:
        """Validates that the incoming state meets the engine's pre-requisites."""
        pass

    @abstractmethod
    async def rollback(self, state: BrainState) -> BrainState:
        """Defines state transitions to execute on failure or exception recovery.

        Cleans up or reverts engine-specific mutations to prevent corrupted
        orchestration transitions.
        """
        pass
