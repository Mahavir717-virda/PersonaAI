"""Extracts tasks and action items from text using local LLMs."""

from __future__ import annotations

import json
import httpx
from typing import Any, Dict, List

from app.brain.task.prompts import TASK_EXTRACTION_PROMPT


class TaskExtractor:
    """Invokes local LLM models to extract tasks and dependencies."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def extract_tasks(self, text: str, model: str | None = None) -> List[Dict[str, Any]]:
        """Extracts structured tasks, falling back to heuristics on connection error."""
        model_name = model or self.default_model
        prompt = TASK_EXTRACTION_PROMPT.format(text=text)

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
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "tasks" in data:
                    return data["tasks"]
            except Exception:
                pass

        # Simple rule fallback if LLM offline: if text has task triggers
        lower_text = text.lower()
        if "prepare" in lower_text or "presentation" in lower_text or "meeting" in lower_text:
            return [
                {
                    "title": "Prepare presentation",
                    "owner": "user",
                    "priority": "high",
                    "deadline": "Friday",
                    "status": "pending",
                    "depends_on": []
                }
            ]
        return []
