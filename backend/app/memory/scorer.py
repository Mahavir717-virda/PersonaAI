"""Combined formula scorer for AI Memory retrieval ranking."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any, Dict
from app.brain.models.brain_models import Memory


class MemoryScorer:
    """Calculates multidimensional relevance scores for retrieved memories."""

    DECAY_CURVES = {
        "working": 1440.0,       # Decays in minutes (fast decay)
        "episodic": 0.05,       # Decays in weeks (medium decay)
        "semantic": 0.005,      # Decays in months (slow decay)
        "procedural": 0.0001,   # Almost never decays
    }

    def __init__(self, decay_constant: float = 0.01, pinning_boost: float = 0.3) -> None:
        self.decay_constant = decay_constant
        self.pinning_boost = pinning_boost

    def score_memory(self, memory: Memory, similarity: float) -> float:
        """Calculates final score incorporating similarity, recency, pinning, and frequency."""
        # 1. Similarity score
        sim_val = max(0.0, min(1.0, similarity))

        # 2. Recency & Decay calculation
        created_time = memory.created_at or datetime.now(timezone.utc)
        if created_time.tzinfo is None:
            created_time = created_time.replace(tzinfo=timezone.utc)
        
        time_delta_seconds = (datetime.now(timezone.utc) - created_time).total_seconds()
        days_since = max(0.0, time_delta_seconds / 86400.0)
        
        # Recency score (decays towards 0 over days)
        recency = 1.0 / (1.0 + days_since)
        
        # Exponential time decay penalty mapped to memory type
        decay_rate = self.DECAY_CURVES.get(memory.memory_type, self.decay_constant)
        decay = -1.0 * (1.0 - math.exp(-decay_rate * days_since))

        # 3. Metadata attributes: Importance, Pinning, and Frequency
        meta = memory.metadata_ or {}
        
        # Importance score (defaults to 0.5)
        importance = float(meta.get("importance", 0.5))
        
        # Access frequency log boost
        access_count = int(meta.get("access_count", 0))
        access_frequency = 0.1 * math.log1p(access_count)
        
        # User pinning boost
        is_pinned = bool(meta.get("pinned", False))
        user_pinning = self.pinning_boost if is_pinned else 0.0

        # 4. Extraction confidence
        confidence = float(memory.confidence if memory.confidence is not None else 1.0)

        # Combined scoring formula
        final_score = sim_val + recency + importance + access_frequency + user_pinning + confidence + decay
        return max(0.0, final_score)
