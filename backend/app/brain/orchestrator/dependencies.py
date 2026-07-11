"""Dependency Injection Container and Engine Registry for PersonaAI Brain."""

from __future__ import annotations

from typing import Dict

from app.brain.engines.base import BrainEngine
from app.brain.engines.memory import MemoryEngine
from app.brain.knowledge.engine import KnowledgeEngine
from app.brain.engines.reasoning import ReasoningEngine
from app.brain.planning.engine import PlanningEngine
from app.brain.engines.rag import RAGEngine
from app.brain.engines.response import ResponseEngine
from app.brain.engines.learning import LearningEngine
from app.brain.task.engine import TaskEngine
from app.brain.entity.engine import EntityEngine
from app.brain.communication.engine import CommunicationEngine


class BrainContainer:
    """A Dependency Injection container that provides and registers engines."""

    def __init__(self) -> None:
        self._engines: Dict[str, BrainEngine] = {}
        self._initialize_defaults()

    def register(self, name: str, engine: BrainEngine) -> None:
        """Register a custom engine with the container registry."""
        self._engines[name] = engine

    def get(self, name: str) -> BrainEngine:
        """Retrieve a registered engine by its name key."""
        if name not in self._engines:
            raise KeyError(f"Engine '{name}' is not registered in the BrainContainer.")
        return self._engines[name]

    def list_registered_engines(self) -> Dict[str, BrainEngine]:
        """Returns a snapshot dictionary mapping engine names to instances."""
        return dict(self._engines)

    def _initialize_defaults(self) -> None:
        """Registers default stub engine implementations."""
        self.register("memory", MemoryEngine())
        self.register("knowledge", KnowledgeEngine())
        self.register("reasoning", ReasoningEngine())
        self.register("planning", PlanningEngine())
        self.register("rag", RAGEngine())
        self.register("response", ResponseEngine())
        self.register("learning", LearningEngine())
        self.register("task", TaskEngine())
        self.register("entity", EntityEngine())
        self.register("communication", CommunicationEngine())
