"""AI Provider Factory."""

from app.config import get_settings
from app.ai.providers.base import BaseAIProvider
from app.ai.providers.groq_provider import GroqProvider
from app.ai.providers.ollama_provider import OllamaProvider
from app.ai.providers.huggingface_provider import HuggingFaceProvider
from app.ai.providers.persona_provider import PersonaProvider
from app.ai.exceptions.provider_exception import ProviderError

class AIProviderFactory:
    """Factory to instantiate AI providers based on application configuration."""

    @staticmethod
    def get_provider(provider_name: str | None = None) -> BaseAIProvider:
        """Instantiates and returns the configured AI provider."""
        settings = get_settings()
        active_provider = (provider_name or settings.ai_provider or "").lower().strip()

        if not active_provider:
            raise ProviderError("AI provider is not configured. Please set AI_PROVIDER.")

        if active_provider == "groq":
            return GroqProvider(
                api_key=settings.groq_api_key,
                model=settings.ai_model or "llama3-8b-8192"
            )
        elif active_provider == "ollama":
            return OllamaProvider(
                base_url=settings.ollama_base_url or "http://localhost:11434",
                model=settings.ai_model or settings.ollama_model or "llama3.2"
            )
        elif active_provider == "huggingface":
            return HuggingFaceProvider(api_key=None)
        elif active_provider == "persona":
            return PersonaProvider()
        else:
            raise ProviderError(f"Unsupported AI provider: {active_provider}")
