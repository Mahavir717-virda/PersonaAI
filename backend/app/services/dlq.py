"""Dead Letter Queue service implementation."""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)


class DeadLetterQueueService:
    """Manages archiving and retry tracing of unprocessable or corrupted message payloads."""

    def __init__(self, dlq_dir: str = "f:/PersonaAI/storage_data/dlq") -> None:
        self.dlq_dir = Path(dlq_dir)
        os.makedirs(self.dlq_dir, exist_ok=True)

    async def send_to_dlq(self, platform: str, payload: Dict[str, Any], reason: str) -> str:
        """Serialize and save bad payload to DLQ directory."""
        filename = f"{platform}_{payload.get('id', 'unknown')}_{int(os.getpid())}.json"
        file_path = self.dlq_dir / filename
        
        dlq_record = {
            "platform": platform,
            "failed_reason": reason,
            "raw_payload": payload,
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dlq_record, f, indent=2)

        logger.warning(f"[DLQ] Bad payload saved to DLQ: {filename}. Reason: {reason}")
        return str(file_path.as_posix())
