"""Post-processes generated model JSON payloads, ensuring schema validation and repair."""

from __future__ import annotations

import json
from typing import Dict, Any


class SummaryPostProcessor:
    """Cleans up markdown blocks and repairs missing properties inside LLM JSON outputs."""

    @staticmethod
    def clean_and_repair_json(raw_output: str) -> Dict[str, Any]:
        """Strips markdown identifiers and maps missing fields to guarantee schema conformity."""
        if not raw_output:
            return {}

        cleaned = raw_output.strip()

        # 1. Strip markdown wrapper blocks
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
        except Exception:
            # Simple bracket match repair attempt
            try:
                start = cleaned.find("{")
                end = cleaned.rfind("}")
                if start != -1 and end != -1:
                    parsed = json.loads(cleaned[start:end+1])
                else:
                    parsed = {}
            except Exception:
                parsed = {}

        if not isinstance(parsed, dict):
            parsed = {}

        # 2. Guarantee all schema keys exist as lists/strings
        default_fields = {
            "tldr": "",
            "summary": "No summary generated.",
            "key_points": [],
            "decisions": [],
            "action_items": [],
            "deadlines": [],
            "people": [],
            "organizations": [],
            "projects": [],
            "meetings": [],
            "risks": [],
            "follow_ups": [],
            "questions": [],
            "topics": []
        }

        final_data = {}
        for key, default in default_fields.items():
            val = parsed.get(key)
            if isinstance(default, list):
                final_data[key] = list(val) if isinstance(val, list) else []
            else:
                final_data[key] = str(val) if val is not None else default

        return final_data
