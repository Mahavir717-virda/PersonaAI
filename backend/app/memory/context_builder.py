"""Memory Context Builder to format and optimize memory context injected into LLM prompts."""

from __future__ import annotations

from typing import Dict, List
from app.brain.models.brain_models import Memory


class MemoryContextBuilder:
    """Formats and summarizes retrieved memories into a clean string to prevent context token bloat."""

    @staticmethod
    def build_context(
        working: List[str],
        episodic: List[str],
        semantic: List[str],
        procedural: List[str],
        top_k: int = 5,
    ) -> str:
        """Filters top records and structures them into a readable context block."""
        # Limit items to prevent prompt overflow
        working_slice = working[:top_k]
        episodic_slice = episodic[:top_k]
        semantic_slice = semantic[:top_k]
        procedural_slice = procedural[:top_k]

        sections = []

        if working_slice:
            sections.append("### Active Session Context (Working Memory):\n" + "\n".join(f"- {item}" for item in working_slice))
        if episodic_slice:
            sections.append("### Recent Events (Episodic Memory):\n" + "\n".join(f"- {item}" for item in episodic_slice))
        if semantic_slice:
            sections.append("### Key Facts & Profile Associations (Semantic Memory):\n" + "\n".join(f"- {item}" for item in semantic_slice))
        if procedural_slice:
            sections.append("### Response Constraints & Behavioral Preferences (Procedural Memory):\n" + "\n".join(f"- {item}" for item in procedural_slice))

        if not sections:
            return "No relevant memories found."

        return "\n\n".join(sections)
