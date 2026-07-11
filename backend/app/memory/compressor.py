"""Memory Compressor for consolidating historical memories in PersonaAI."""

from __future__ import annotations

from typing import List
import httpx

from app.brain.models.brain_models import Memory


class MemoryCompressor:
    """Consolidates large batches of memories into unified summaries to optimize context window storage."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def compress_memories(self, memories: List[Memory], model: str | None = None) -> str:
        """Consolidates a list of memories into a single structured summary using local Ollama model."""
        if not memories:
            return ""

        model_name = model or self.default_model
        
        # Compile list of memories into text prompt
        memory_texts = [f"- [{m.memory_type}] {m.content}" for m in memories]
        compiled_list = "\n".join(memory_texts)
        
        prompt = (
            "Analyze the following list of user memories and write a concise, unified summary "
            "consolidating all key facts, preferences, and events. Maintain details like names, roles, and dates.\n\n"
            f"Memories:\n{compiled_list}\n\n"
            "Summary:"
        )

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=60.0,
                )
                response.raise_for_status()
                data = response.json()
                return str(data["response"]).strip()
            except Exception:
                # Fallback to simple concatenation if local LLM is offline or times out
                return f"Summary of memories: {'; '.join([m.content for m in memories])}"
