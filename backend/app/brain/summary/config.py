"""Settings configuration for the Summary Model Subsystem."""

import os

# Default model path pointing to local fine-tuned QLoRA weights
SUMMARY_MODEL_PATH = os.environ.get("SUMMARY_MODEL_PATH", "backend/app/models/summary/PersonaAI_LoRA_Export_V1")

# Max token response length constraint
SUMMARY_MAX_NEW_TOKENS = int(os.environ.get("SUMMARY_MAX_NEW_TOKENS", "1024"))

# Inference timeout protection in seconds
SUMMARY_INFERENCE_TIMEOUT = float(os.environ.get("SUMMARY_INFERENCE_TIMEOUT", "30.0"))
