"""Dynamic Node Router for PersonaAI LangGraph StateGraph orchestration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from app.brain.schemas.state import BrainState


class BrainRouter:
    """Dynamic routing router that evaluates State variables to decide next nodes."""

    @staticmethod
    def route_after_memory(state: BrainState) -> Literal["knowledge", "response"]:
        """Decides whether to route to knowledge engine or skip straight to response."""
        # Example condition: if intent is a simple greeting, we can skip search.
        if state.communication_intelligence.intent == "greeting":
            return "response"
        return "knowledge"

    @staticmethod
    def route_after_planning(state: BrainState) -> Literal["rag", "response"]:
        """Decides if the reasoning plan requires RAG search or moves to response generation."""
        if not state.planning.planned_actions and not state.tool_calling.enabled_tools:
            return "response"
        return "rag"

    @staticmethod
    def route_after_response(state: BrainState) -> Literal["learning", "START", "__end__"]:
        """Evaluates post-generation reflection to determine if execution needs to loop back or terminate."""
        reflection = state.response.reflection
        
        # If the reflection says retrieval was insufficient or another search cycle is required,
        # we can route back to memory/planning or retry. To prevent infinite loops, we cap depth.
        if reflection.needs_more_search and state.execution.execution_depth < 3:
            return "START"
            
        # Standard flow moves to learning and persistence phase.
        return "learning"
