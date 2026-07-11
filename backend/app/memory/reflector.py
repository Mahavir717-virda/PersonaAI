"""AI Memory Reflector for evaluation and importance prediction."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional
import httpx


class MemoryReflector:
    """Evaluates conversation turns using local LLMs to extract standalone memories and predict importance."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def reflect(self, input_text: str, response_text: str, model: str | None = None) -> Optional[Dict[str, Any]]:
        """Invokes local Ollama model to determine if the interaction contains facts to remember, returning metadata."""
        model_name = model or self.default_model
        
        prompt = (
            "Analyze the conversation turn. Determine if there is any long-term fact, "
            "user preference, process guideline, or important event that the AI should permanently remember.\n\n"
            f"User: {input_text}\n"
            f"AI: {response_text}\n\n"
            "Respond in JSON format with keys:\n"
            "- should_remember: boolean\n"
            "- content_to_remember: string (clear standalone fact statement, e.g. 'John is user's manager')\n"
            "- memory_type: string ('episodic', 'semantic', 'procedural', or 'working')\n"
            "- importance: number (0.0 to 1.0, e.g. 0.99 for birthdays/vital data, 0.03 for generic chat)\n\n"
            "JSON Response:"
        )

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
                
                if data.get("should_remember", False) and data.get("content_to_remember"):
                    return {
                        "content": data["content_to_remember"],
                        "memory_type": data.get("memory_type", "semantic"),
                        "importance": float(data.get("importance", 0.5)),
                    }
            except Exception:
                # Rule-based fallback if LLM offline
                lower_text = input_text.lower()
                # Birthdays get very high importance, manager names high, generic low
                if "birthday" in lower_text:
                    return {
                        "content": input_text,
                        "memory_type": "semantic",
                        "importance": 0.99,
                    }
                elif "my manager is" in lower_text:
                    return {
                        "content": input_text,
                        "memory_type": "semantic",
                        "importance": 0.85,
                    }
                elif "prefers" in lower_text:
                    return {
                        "content": input_text,
                        "memory_type": "procedural",
                        "importance": 0.75,
                    }

            return None
