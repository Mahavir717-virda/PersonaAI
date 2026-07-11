"""Extracts structural entities from conversation text using local LLMs."""

from __future__ import annotations

import json
import httpx
from typing import Any, Dict, List

from app.brain.entity.prompts import ENTITY_EXTRACTION_PROMPT


class EntityExtractor:
    """Invokes local LLM models to extract detailed entity segments."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def extract_entities(self, text: str, model: str | None = None) -> List[Dict[str, Any]]:
        """Invokes LLM extraction prompt, falling back to heuristic parsing if connection fails."""
        model_name = model or self.default_model
        prompt = ENTITY_EXTRACTION_PROMPT.format(text=text)

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
                if isinstance(data, dict) and "entities" in data:
                    return data["entities"]
            except Exception:
                pass

        # Simple fallback heuristic: Capitalized words
        fallbacks = []
        words = text.split()
        for i, word in enumerate(words):
            if word[0].isupper() and i > 0 and len(word) > 1:
                clean_name = word.strip(".,;:?!'\"")
                fallbacks.append({
                    "value": clean_name,
                    "type": "Concept",
                    "start_char": text.find(clean_name),
                    "end_char": text.find(clean_name) + len(clean_name),
                    "canonical_name": clean_name,
                    "confidence": 0.6,
                })
        return fallbacks
