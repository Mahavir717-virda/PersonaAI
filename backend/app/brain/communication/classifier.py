"""Orchestrates LLM calls to classify communication details."""

from __future__ import annotations

import json
import httpx
from typing import Any, Dict

from app.brain.communication.prompts import COMMUNICATION_CLASSIFICATION_PROMPT
from app.brain.communication.intent import IntentDetector
from app.brain.communication.urgency import UrgencyDetector
from app.brain.communication.priority import PriorityDetector
from app.brain.communication.tone import ToneDetector
from app.brain.communication.emotion import EmotionDetector
from app.brain.communication.category import CategoryDetector
from app.brain.communication.reply_detector import ReplyDetector
from app.brain.communication.confidence import ConfidenceCalculator


class CommunicationClassifier:
    """Invokes local LLM models to retrieve structured classifications for a user message."""

    def __init__(self, base_url: str = "http://localhost:11434", default_model: str = "llama3.1") -> None:
        self.base_url = base_url
        self.default_model = default_model

    async def classify(self, text: str, model: str | None = None) -> Dict[str, Any]:
        """Calls LLM to fetch properties, falling back to clean rule heuristics if needed."""
        model_name = model or self.default_model
        prompt = COMMUNICATION_CLASSIFICATION_PROMPT.format(text=text)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                    },
                    timeout=30.0,
                )
                response.raise_for_status()
                data = json.loads(response.json()["response"])
                
                # Validate and standardize response schema
                return {
                    "intent": IntentDetector.clean_intent(data.get("intent")),
                    "emotion": EmotionDetector.clean_emotion(data.get("emotion")),
                    "urgency": UrgencyDetector.clean_urgency(data.get("urgency")),
                    "priority": PriorityDetector.clean_priority(data.get("priority")),
                    "tone": ToneDetector.clean_tone(data.get("tone")),
                    "category": CategoryDetector.clean_category(data.get("category")),
                    "requires_reply": bool(data.get("requires_reply", False)),
                    "contains_task": bool(data.get("contains_task", False)),
                    "contains_deadline": bool(data.get("contains_deadline", False)),
                    "contains_decision": bool(data.get("contains_decision", False)),
                    "contains_meeting": bool(data.get("contains_meeting", False)),
                    "confidence": ConfidenceCalculator.calculate_confidence(data.get("confidence")),
                }
            except Exception:
                pass

        # Robust heuristic fallback when local LLM is offline or output is invalid
        heuristics = ReplyDetector.evaluate_triggers(text)
        
        # Simple defaults for sentiment properties
        intent = "unknown"
        if heuristics["contains_task"]:
            intent = "request"
        elif "?" in text:
            intent = "question"

        return {
            "intent": intent,
            "emotion": "neutral",
            "urgency": "medium" if (heuristics["contains_deadline"] or heuristics["contains_task"]) else "low",
            "priority": "high" if heuristics["contains_deadline"] else "medium",
            "tone": "urgent" if heuristics["contains_deadline"] else "neutral",
            "category": "work" if (heuristics["contains_task"] or heuristics["contains_meeting"]) else "general",
            "requires_reply": heuristics["requires_reply"],
            "contains_task": heuristics["contains_task"],
            "contains_deadline": heuristics["contains_deadline"],
            "contains_decision": heuristics["contains_decision"],
            "contains_meeting": heuristics["contains_meeting"],
            "confidence": 0.5,
        }
