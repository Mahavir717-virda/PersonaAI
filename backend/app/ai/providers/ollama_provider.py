"""Ollama AI Provider implementation."""

from typing import AsyncGenerator
import httpx

from app.ai.providers.base import BaseAIProvider
from app.ai.exceptions.provider_exception import (
    ProviderAPIError,
    ProviderTimeoutError,
    ProviderError,
)

class OllamaProvider(BaseAIProvider):
    """Integrates local Ollama instance over REST API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _map_exception(self, e: Exception) -> Exception:
        if isinstance(e, httpx.TimeoutException):
            return ProviderTimeoutError(str(e))
        elif isinstance(e, httpx.HTTPStatusError):
            return ProviderAPIError(message=f"Ollama server returned {e.response.status_code}", status_code=e.response.status_code)
        elif isinstance(e, ProviderError):
            return e
        return ProviderAPIError(message=f"Ollama connection error: {str(e)}")

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        model = kwargs.pop("model", self.model)
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            **kwargs
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
        except Exception as e:
            raise self._map_exception(e)

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        model = kwargs.pop("model", self.model)
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            **kwargs
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if line:
                            import json
                            try:
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except ValueError:
                                continue
        except Exception as e:
            raise self._map_exception(e)

    async def embeddings(self, text: str) -> list[float]:
        payload = {
            "model": self.model,
            "prompt": text
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.base_url}/api/embeddings", json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("embedding", [])
        except Exception as e:
            raise self._map_exception(e)

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
