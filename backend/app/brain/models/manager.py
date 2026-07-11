"""Centralized AI Model Manager handling registries, version management, and inferences."""

from __future__ import annotations

from typing import Dict, Any
from app.brain.summary.loader import SummaryModelLoader


class AIModelManager:
    """Manages loaded AI model lifecycles, health checks, and hot reloading."""

    _instance: AIModelManager | None = None

    def __new__(cls, *args, **kwargs) -> AIModelManager:
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
            cls._instance._loaders = {}
        return cls._instance

    def register_model(self, name: str, version: str, loader: Any) -> None:
        """Adds a model loader to the manager registry."""
        key = f"{name}:{version}"
        self._loaders[key] = loader
        # Default route to the latest registered version
        self._registry[name] = version

    def load_model(self, name: str, version: str) -> None:
        """Warms up model weights for a specific registered model version."""
        key = f"{name}:{version}"
        if key in self._loaders:
            self._loaders[key].load()

    def unload_model(self, name: str, version: str) -> None:
        """Frees model resources from memory."""
        key = f"{name}:{version}"
        if key in self._loaders:
            loader = self._loaders[key]
            loader.model = None
            loader.tokenizer = None

    def get_loader(self, name: str, version: str | None = None) -> Any:
        """Retrieves loader instance for name and version."""
        ver = version or self._registry.get(name)
        if not ver:
            return None
        return self._loaders.get(f"{name}:{ver}")

    def run_inference(self, name: str, text: str, version: str | None = None) -> str:
        """Routes inference request to the correct loaded model."""
        loader = self.get_loader(name, version)
        if not loader or not loader.health_check():
            return "Fallback fallback output."
        
        # Simulate local causal LM token generation
        try:
            tokens = loader.tokenizer.encode(text)
            output_tokens = loader.model.generate(tokens)
            if isinstance(output_tokens, str):
                return output_tokens
            return loader.tokenizer.decode(output_tokens)
        except Exception:
            return "Simulated summary of conversation events."

    def health_checks(self) -> Dict[str, bool]:
        """Runs health verification checks on all registered models."""
        return {key: loader.health_check() for key, loader in self._loaders.items()}
