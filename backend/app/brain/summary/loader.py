"""Loads local model weights and tokenizers for Summary Model V1."""

from __future__ import annotations

import os
import logging
from typing import Any
from app.brain.summary.config import SUMMARY_MODEL_PATH

logger = logging.getLogger(__name__)


class MockSummaryModel:
    """Mock model simulating casual LM inference when offline or local weights are absent."""

    def generate(self, *args, **kwargs) -> Any:
        import json
        return json.dumps({
            "tldr": "Conversational summary of request context.",
            "summary": "This is a detailed mock summary of conversation events.",
            "key_points": ["Point 1", "Point 2"],
            "decisions": [],
            "action_items": ["Review Project Atlas"],
            "deadlines": [],
            "people": ["Sarah"],
            "organizations": [],
            "projects": ["Project Atlas"],
            "meetings": [],
            "risks": [],
            "follow_ups": [],
            "questions": [],
            "topics": ["Work"]
        })


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
        self.model_path = model_path or SUMMARY_MODEL_PATH
        self.model = None
        self.tokenizer = None
        self._initialized = True

    def load(self) -> None:
        """Loads weights from model_path, falling back to Mock if directory is missing."""
        # Dynamically compute absolute path relative to this file to handle any working directory
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_file_dir, "..", "..", ".."))
        
        # Check environment variable first, then fallback to absolute project root path
        env_path = os.environ.get("SUMMARY_MODEL_PATH")
        target_path = env_path if env_path else os.path.join(project_root, "app", "models", "summary", "PersonaAI_LoRA_Export_V1")

        if os.path.exists(target_path) and os.path.isdir(target_path):
            try:
                from transformers import AutoTokenizer, AutoModelForCausalLM
                self.tokenizer = AutoTokenizer.from_pretrained(target_path)
                
                # Check if it is a LoRA adapter config
                if os.path.exists(os.path.join(target_path, "adapter_config.json")):
                    from peft import PeftModel
                    import torch
                    from transformers import BitsAndBytesConfig
                    
                    base_model_name = "unsloth/Llama-3.2-1B-Instruct-bnb-4bit"
                    
                    if torch.cuda.is_available():
                        try:
                            # 1. Try loading with automatic GPU device mapping
                            base_model = AutoModelForCausalLM.from_pretrained(
                                base_model_name,
                                device_map="auto",
                                low_cpu_mem_usage=True
                            )
                        except Exception:
                            # 2. Try loading with CPU offloading fallback if GPU RAM is low
                            bnb_config = BitsAndBytesConfig(
                                load_in_4bit=True,
                                llm_int8_enable_fp32_cpu_offload=True
                            )
                            base_model = AutoModelForCausalLM.from_pretrained(
                                base_model_name,
                                quantization_config=bnb_config,
                                device_map="auto",
                                low_cpu_mem_usage=True
                            )
                    else:
                        # 3. Fallback to CPU-only execution (raises to trigger Mock loader)
                        raise RuntimeError("CUDA is required to run Llama-3.2 4-bit model.")
                        
                    self.model = PeftModel.from_pretrained(base_model, target_path)
                else:
                    self.model = AutoModelForCausalLM.from_pretrained(target_path)
            except Exception as e:
                # Capture any model/quantization loading issue and fall back to Mock
                logger.error("Failed to load local model weights. Falling back to Mock.", exc_info=True)
                self.model = MockSummaryModel()
                self.tokenizer = MockTokenizer()
        else:
            # Fallback simulator
            self.model = MockSummaryModel()
            self.tokenizer = MockTokenizer()

    def health_check(self) -> bool:
        """Verifies if model & tokenizer are warmed up."""
        return self.model is not None and self.tokenizer is not None


summary_model_loader = SummaryModelLoader()

