"""Manages Knowledge Graph versioning and fact supersession tracking."""

from __future__ import annotations

from typing import Any, Dict
from uuid import UUID
from datetime import datetime, timezone

from app.brain.models.brain_models import Knowledge


class KnowledgeVersioning:
    """Handles logic to mark older facts as superseded when new conflicting information is validated."""

    @staticmethod
    def supersede_fact(
        old_knowledge: Knowledge,
        new_knowledge_id: UUID,
        reason: str | None = None
    ) -> Knowledge:
        """Flags an old knowledge node as superseded, linking it to the active version."""
        meta = dict(old_knowledge.metadata_ or {})
        
        # Track versioning indicators in metadata
        meta["superseded"] = True
        meta["superseded_by_id"] = str(new_knowledge_id)
        meta["superseded_at"] = datetime.now(timezone.utc).isoformat()
        meta["supersede_reason"] = reason or "Superseded by newer incoming fact."

        old_knowledge.metadata_ = meta
        old_knowledge.updated_at = datetime.now(timezone.utc)
        return old_knowledge
