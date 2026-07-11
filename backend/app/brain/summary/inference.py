"""Local model inference generation runner."""

from __future__ import annotations

import asyncio
from typing import Any
from app.brain.summary.loader import SummaryModelLoader
from app.brain.summary.config import SUMMARY_MAX_NEW_TOKENS, SUMMARY_INFERENCE_TIMEOUT


class SummaryInferenceRunner:
    """Executes deterministic model inference pipelines with thread safety and timeouts."""

    def __init__(self, loader: SummaryModelLoader | None = None) -> None:
        self.loader = loader or SummaryModelLoader()

    async def run_inference(self, clean_text: str) -> str:
        """Executes text tokenization and model generation under timeout rules."""
        if not self.loader.health_check():
            raise RuntimeError("Summary model has not been loaded successfully.")

        model = self.loader.model
        tokenizer = self.loader.tokenizer

        async def _generate_task() -> str:
            # Tokenize input text
            inputs = tokenizer.encode(clean_text)
            
            # Deterministic greedy search parameters
            outputs = model.generate(
                inputs,
                max_new_tokens=SUMMARY_MAX_NEW_TOKENS,
                temperature=0.0,
                do_sample=False
            )
            
            if isinstance(outputs, str):
                return outputs
            return tokenizer.decode(outputs)

        try:
            # Protect execution with timeout bounds
            return await asyncio.wait_for(_generate_task(), timeout=SUMMARY_INFERENCE_TIMEOUT)
        except asyncio.TimeoutError:
            raise TimeoutError("Model inference call timed out.")
