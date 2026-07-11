"""Implementation of the CommunicationEngine."""

from __future__ import annotations

from app.brain.engines.base import BrainEngine
from app.brain.schemas.state import BrainState, CommunicationIntelligence
from app.brain.communication.classifier import CommunicationClassifier


class CommunicationEngine(BrainEngine):
    """Communication Intelligence Engine evaluating intents, urgency levels, tones, and triggers."""

    def __init__(self, classifier: CommunicationClassifier | None = None) -> None:
        self.classifier = classifier or CommunicationClassifier()

    @property
    def name(self) -> str:
        return "communication"

    async def execute(self, state: BrainState) -> BrainState:
        incoming = state.conversation.incoming_message
        if not incoming or not incoming.content:
            return state

        # 1. Run full classification
        res = await self.classifier.classify(
            text=incoming.content,
            model=state.model_routing.selected_model,
        )

        # 2. Update state.communication_intelligence sub-state
        new_comm_state = CommunicationIntelligence(
            intent=res["intent"],
            emotion=res["emotion"],
            urgency=res["urgency"],
            priority=res["priority"],
            tone=res["tone"],
            category=res["category"],
            requires_reply=res["requires_reply"],
            contains_task=res["contains_task"],
            contains_deadline=res["contains_deadline"],
            contains_decision=res["contains_decision"],
            contains_meeting=res["contains_meeting"],
            confidence=res["confidence"],
        )

        return state.update(communication_intelligence=new_comm_state)

    async def validate(self, state: BrainState) -> bool:
        return True

    async def rollback(self, state: BrainState) -> BrainState:
        return state
