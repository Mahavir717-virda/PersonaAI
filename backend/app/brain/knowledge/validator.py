"""Validates facts and resolves conflicts between incoming and existing graph nodes."""

from __future__ import annotations

import json
import httpx
from typing import Any, Dict, Optional

from app.brain.knowledge.prompts import CONFLICT_RESOLUTION_PROMPT


class FactValidator:
    """Invokes local LLM models to resolve conflicts between historical and incoming facts."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def resolve_conflict(
        self,
        existing_fact: str,
        incoming_fact: str,
        model: str | None = None
    ) -> Dict[str, Any]:
        """Resolves conflict between two facts, determining if one is superseded or if they should be merged."""
        model_name = model or self.default_model
        prompt = CONFLICT_RESOLUTION_PROMPT.format(fact_a=existing_fact, fact_b=incoming_fact)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = json.loads(response.json()["response"])
                return data
            except Exception:
                # If LLM offline, simple rule-based fallback:
                # If content is different, default to letting the new fact supersede the old fact
                return {
                    "has_conflict": True,
                    "resolution": "supersede_a_with_b",
                    "merged_content": "",
                    "explanation": "Rule-based fallback: incoming fact took precedence."
                }
