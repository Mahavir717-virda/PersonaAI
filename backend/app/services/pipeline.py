"""Communication processing pipeline implementation."""

import base64
import logging
import uuid
from typing import Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.factory import ConnectorFactory
from app.repositories.communication import CommunicationRepository
from app.services.storage import StorageService
from app.services.indexer import PostgresIndexer
from app.services.dlq import DeadLetterQueueService
from app.services.ai_queue import AIQueue
from app.events.events import MessageImported
from app.models.communication import Communication
from app.schemas.pipeline import ProcessPayloadResult
from app.events.bus import event_bus

logger = logging.getLogger(__name__)


class PipelineValidationError(Exception):
    """Raised when validation constraints fail on incoming raw payloads."""
    pass


class CommunicationPipeline:
    """Orchestrates message processing: Normalizer -> Validator -> Deduplicator -> Storage -> Indexer -> Event Bus -> AI Queue."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._comm_repo = CommunicationRepository(session)
        self.storage_service = StorageService(session)
        self.indexer = PostgresIndexer()
        self.dlq_service = DeadLetterQueueService()
        self.ai_queue = AIQueue()

    @staticmethod
    def _decode_attachment_content(raw_attachment: Dict[str, Any]) -> bytes | None:
        """Decode attachment content from provider payloads into raw bytes."""
        content = raw_attachment.get("content")
        if isinstance(content, bytes):
            return content
        if isinstance(content, str) and content:
            return content.encode("utf-8")

        encoded = raw_attachment.get("content_base64")
        if isinstance(encoded, str) and encoded:
            padding = "=" * (-len(encoded) % 4)
            return base64.urlsafe_b64decode(encoded + padding)
        return None

    async def process_payload(
        self,
        platform_str: str,
        raw_data: Dict[str, Any],
        connector_id: uuid.UUID | None = None,
    ) -> ProcessPayloadResult | None:
        """Execute the ingestion pipeline for a single raw message payload."""
        platform_key = platform_str.upper()
        step = "start"
        try:
            # 1. Normalizer (translate to Communication model)
            step = "normalize"
            connector = ConnectorFactory.create(platform_key)
            comm = await connector.normalize(raw_data)
            if connector_id is not None:
                comm.connector_id = connector_id

            attachment_count = len(raw_data.get("attachments", []))

            # 2. Validator
            step = "validate"
            if not comm.body or not comm.platform_message_id:
                raise PipelineValidationError("Validation failed: Message body or ID is missing")

            # 3. Deduplicator
            step = "deduplicate"
            exists = await self._comm_repo.get_by_platform_message_id(
                comm.platform,
                comm.platform_message_id,
                connector_id=connector_id,
            )
            if exists:
                logger.info(f"[Pipeline] Deduplicated: message {comm.platform_message_id} already exists.")
                return ProcessPayloadResult(
                    communication_id=exists.id,
                    attachment_count=attachment_count,
                    is_new=False,
                )

            # 4. Storage & DB write
            step = "persist"
            # Create thread conversation if needed
            thread_id = raw_data.get("thread_id") or raw_data.get("id")
            conversation = await self._comm_repo.get_or_create_conversation(comm.platform, thread_id)
            comm.conversation_id = conversation.id

            await self._comm_repo.create_communication(comm)
            
            # Save attachments to file storage and database
            step = "attachments"
            for raw_att in raw_data.get("attachments", []):
                attachment_bytes = self._decode_attachment_content(raw_att)
                if attachment_bytes is None:
                    logger.warning(
                        "[Pipeline] Skipping attachment without content for message %s",
                        comm.platform_message_id,
                    )
                    continue
                await self.storage_service.save_attachment(
                    communication_id=comm.id,
                    filename=raw_att["name"],
                    content=attachment_bytes,
                    content_type=raw_att.get("content_type"),
                )

            # 5. Indexer
            step = "index"
            await self.indexer.index(comm)

            # 6. Event Publisher
            step = "publish"
            event = MessageImported(
                message_id=comm.id,
                platform_message_id=comm.platform_message_id,
                platform=comm.platform.name,
            )
            await event_bus.publish(event)

            # 7. AI Queue (Async pipeline)
            step = "queue"
            await self.ai_queue.enqueue_task(str(comm.id), raw_data)

            return ProcessPayloadResult(
                communication_id=comm.id,
                attachment_count=attachment_count,
                is_new=True,
            )

        except Exception as e:
            logger.error(
                "[Pipeline] Processing failed for platform %s at step %s: %s",
                platform_str,
                step,
                str(e),
                exc_info=True,
            )
            # Route to Dead Letter Queue (DLQ) so sync loops do not crash
            await self.dlq_service.send_to_dlq(platform_str, raw_data, str(e))
            return None
