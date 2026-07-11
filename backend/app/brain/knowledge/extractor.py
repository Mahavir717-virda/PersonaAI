"""Extracts entities and relationships from conversation text."""

from __future__ import annotations

import json
import httpx
from typing import Any, Dict, List, Tuple

from app.brain.knowledge.prompts import ENTITY_EXTRACTION_PROMPT, RELATIONSHIP_EXTRACTION_PROMPT


class KnowledgeExtractor:
    """Invokes local LLM models to extract entities and relationship triples."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def extract_entities(self, text: str, model: str | None = None) -> List[Dict[str, Any]]:
        """Extracts structured entities (Person, Project, Location, etc.) from text."""
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

        # Rule-based fallback if LLM is offline or output is invalid JSON
        fallback_entities = []
        words = text.split()
        for i, word in enumerate(words):
            # Extremely simple named entity recognition heuristic: Capitalized words (excluding first word of sentence)
            if word[0].isupper() and i > 0 and len(word) > 1:
                clean_name = word.strip(".,;:?!'\"")
                fallback_entities.append({
                    "name": clean_name,
                    "type": "Concept",
                    "properties": {}
                })
        return fallback_entities

    async def extract_relationships(self, text: str, model: str | None = None) -> List[Dict[str, Any]]:
        """Extracts structured subject-predicate-object relationship triples from text."""
        model_name = model or self.default_model
        prompt = RELATIONSHIP_EXTRACTION_PROMPT.format(text=text)

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
                if isinstance(data, dict) and "relationships" in data:
                    return data["relationships"]
            except Exception:
                pass

        # Fallback empty list if local Ollama model fails
        return []
