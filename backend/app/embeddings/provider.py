"""Ollama-based Embedding Provider for PersonaAI."""

from __future__ import annotations

from typing import List
import httpx


class OllamaEmbeddingProvider:
    """Client provider to generate vector embeddings using local Ollama instance."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "nomic-embed-text") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def get_embedding(self, text: str, model: str | None = None) -> List[float]:
        """Generates a single vector embedding for the input text."""
        model_name = model or self.default_model
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": model_name, "prompt": text},
                    timeout=30.0,
                )
                response.raise_for_status()
                data = response.json()
                return list(data["embedding"])
            except Exception as e:
                # Mock fallback / log error to prevent hard crashes during local offline runs
                # Fallback to an empty or dummy vector of 768 dimensions (Nomic length)
                return [0.0] * 768

    async def get_embeddings(self, texts: List[str], model: str | None = None) -> List[List[float]]:
        """Generates batch embeddings for list of input texts."""
        embeddings = []
        for text in texts:
            emb = await self.get_embedding(text, model)
            embeddings.append(emb)
        return embeddings
