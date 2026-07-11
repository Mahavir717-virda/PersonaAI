"""Groq AI Provider implementation."""

from typing import AsyncGenerator
import groq
from groq import AsyncGroq

from app.ai.providers.base import BaseAIProvider
from app.ai.exceptions.provider_exception import (
    ProviderAPIError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderError,
)

class GroqProvider(BaseAIProvider):
    """Integrates official Groq SDK client for chat completions and streaming."""

    def __init__(self, api_key: str | None, model: str = "llama3-8b-8192") -> None:
        if not api_key or api_key == "Your_API_Key" or api_key.strip() == "":
            raise ProviderAuthenticationError("Groq API key is missing or invalid.")
        self.api_key = api_key
        self.model = model
        self.client = AsyncGroq(api_key=api_key)

    def _map_exception(self, e: Exception) -> Exception:
        """Map Groq SDK internal exceptions to custom provider exceptions."""
        if isinstance(e, groq.AuthenticationError):
            return ProviderAuthenticationError(str(e))
        elif isinstance(e, groq.RateLimitError):
            return ProviderRateLimitError(str(e))
        elif isinstance(e, groq.APITimeoutError):
            return ProviderTimeoutError(str(e))
        elif isinstance(e, groq.APIStatusError):
            return ProviderAPIError(message=str(e), status_code=e.status_code)
        elif isinstance(e, groq.APIError):
            return ProviderAPIError(message=str(e))
        elif isinstance(e, ProviderError):
            return e
        return ProviderAPIError(message=f"Unexpected provider error: {str(e)}")

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        try:
            model = kwargs.pop("model", self.model)
            response = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                **kwargs
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise self._map_exception(e)

    async def stream_chat(self, messages: list[dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        try:
            model = kwargs.pop("model", self.model)
            stream = await self.client.chat.completions.create(
                messages=messages,
                model=model,
                stream=True,
                **kwargs
            )
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content is not None:
                    yield content
        except Exception as e:
            raise self._map_exception(e)

    async def embeddings(self, text: str) -> list[float]:
        raise NotImplementedError("Embeddings are not supported by the Groq Provider.")

    async def health(self) -> bool:
        try:
            await self.client.models.list()
            return True
        except Exception:
            return False

    async def vision_chat(
        self,
        text_prompt: str,
        image_base64: str,
        mime_type: str = "image/png",
        model: str = "llama-3.2-90b-vision-preview",
    ) -> str:
        """Send an image + text prompt to a vision-capable model for multimodal analysis."""
        try:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_base64}",
                            },
                        },
                    ],
                }
            ]
            response = await self.client.chat.completions.create(
                messages=messages,
                model=model,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise self._map_exception(e)
