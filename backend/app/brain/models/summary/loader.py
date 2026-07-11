"""Loads local model weights and tokenizers for Summary Model V1."""

from __future__ import annotations

import os
from typing import Any


class MockSummaryModel:
    """Mock model simulating casual LM inference when offline or local weights are absent."""

    def generate(self, *args, **kwargs) -> Any:
        return "Simulated summary of conversation events."


class MockTokenizer:
    """Mock tokenizer simulating vocabulary encoding/decoding."""

    def encode(self, text: str, *args, **kwargs) -> list[int]:
        return [101, 102]

    def decode(self, ids: list[int], *args, **kwargs) -> str:
        return "Simulated model output summary."


class SummaryModelLoader:
    """Singleton loader warming up Summary model weights and tokenizer."""

    _instance: SummaryModelLoader | None = None

    def __new__(cls, *args, **kwargs) -> SummaryModelLoader:
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_path: str | None = None) -> None:
        if self._initialized:
            return
        self.model_path = model_path or os.environ.get("SUMMARY_MODEL_PATH", "backend/app/models/summary/v1")
        self.model = None
        self.tokenizer = None
        self._initialized = True

    def load(self) -> None:
        """Loads weights from model_path, falling back to Mock if directory is missing."""
        if os.path.exists(self.model_path) and os.path.isdir(self.model_path):
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
                self.model = AutoModelForCausalLM.from_pretrained(self.model_path)
            except ImportError:
                self.model = MockSummaryModel()
                self.tokenizer = MockTokenizer()
        else:
            # Fallback simulator
            self.model = MockSummaryModel()
            self.tokenizer = MockTokenizer()

    def health_check(self) -> bool:
        """Verifies if model & tokenizer are warmed up."""
        return self.model is not None and self.tokenizer is not None
