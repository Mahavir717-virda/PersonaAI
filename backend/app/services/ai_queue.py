"""AI Priority-Based Queue worker implementation."""

import asyncio
import logging
import uuid
from typing import Any, Dict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.models.communication import Communication
from app.ai.services.summarizer_service import SummarizerService

logger = logging.getLogger(__name__)

# Global priority queue
_QUEUE: asyncio.PriorityQueue = asyncio.PriorityQueue()
_WORKER_TASK: asyncio.Task | None = None


class AIQueue:
    """Queues message objects for async processing with critical-first priority."""

    async def enqueue_task(self, message_id: str, payload: dict[str, Any]) -> None:
        """Assess priority and enqueue task to background worker."""
        # 1. Determine priority (lower number = higher priority)
        priority = 2  # Default: Normal/Deferred
        
        subject = payload.get("subject", "").lower()
        body = payload.get("body", "").lower()
        sender = payload.get("sender_address", "").lower()
        
        # High priority triggers: Boss, invite, calendar, urgent keywords, github notifications
        high_priority_keywords = ["urgent", "asap", "invoice", "meeting", "interview", "calendar"]
        high_priority_domains = ["github.com", "slack.com", "jira.com", "confluence.com"]
        
        is_high = (
            any(kw in subject or kw in body for kw in high_priority_keywords) or
            any(dom in sender for dom in high_priority_domains) or
            "invitation" in subject
        )
        
        if is_high:
            priority = 1  # High/Immediate
            logger.info("[AIQueue] High priority detected for message %s", message_id)
        
        # 2. Push to queue
        # PriorityQueue elements are sorted by the first item of the tuple
        await _QUEUE.put((priority, (message_id, payload)))
        logger.info(
            "[AIQueue] Enqueued message %s (Priority: %s) to background processing queue.",
            message_id,
            priority,
        )


async def start_ai_worker() -> None:
    """Start the background worker task to process enqueued AI tasks."""
    global _WORKER_TASK
    if _WORKER_TASK is not None:
        logger.warning("[AIQueue] Background worker is already running.")
        return
        
    _WORKER_TASK = asyncio.create_task(_worker_loop())
    logger.info("[AIQueue] Background worker loop started.")


async def stop_ai_worker() -> None:
    """Gracefully cancel and stop the background worker task."""
    global _WORKER_TASK
    if _WORKER_TASK is None:
        return
        
    _WORKER_TASK.cancel()
    try:
        await _WORKER_TASK
    except asyncio.CancelledError:
        pass
    _WORKER_TASK = None
    logger.info("[AIQueue] Background worker loop stopped.")


async def _worker_loop() -> None:
    """Pop tasks from PriorityQueue and process them using the AI Summarizer Service."""
    while True:
        try:
            priority, (message_id_str, payload) = await _QUEUE.get()
            logger.info(
                "[AIQueue Worker] Processing message %s (Priority: %s)",
                message_id_str,
                priority,
            )
            
            # Process inside a dedicated DB session context
            await _process_message_summary(message_id_str)
            
            _QUEUE.task_done()
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception("[AIQueue Worker] Error processing enqueued task: %s", str(e))
            await asyncio.sleep(2)  # Avoid fast-spinning on persistent errors


async def _process_message_summary(message_id_str: str) -> None:
    """Retrieve message from database, fetch summary from LLM, process attachments, and store results."""
    session_gen = get_session()
    session: AsyncSession = await anext(session_gen)
    
    try:
        message_id = uuid.UUID(message_id_str)
        stmt = select(Communication).where(Communication.id == message_id)
        result = await session.execute(stmt)
        comm = result.scalar_one_or_none()
        
        if not comm:
            logger.warning("[AIQueue Worker] Message %s not found in database", message_id_str)
            return

        # --- Stage 1: Email Body Summary ---
        if not comm.summary_text:
            summarizer = SummarizerService()
            email_content = f"Subject: {comm.subject}\nBody: {comm.body}"
            
            logger.info("[AIQueue Worker] Calling SummarizerService for message %s", message_id_str)
            summary_res = await summarizer.summarize_email(email_content)
            
            comm.summary_text = summary_res.summary
            comm.tldr = summary_res.tldr
            
            metadata = comm.metadata_fields or {}
            metadata["structured_summary"] = summary_res.model_dump()
            comm.metadata_fields = metadata
            
            session.add(comm)
            await session.commit()
            logger.info("[AIQueue Worker] Email summary stored for message %s", message_id_str)

        # --- Stage 2: Attachment Processing ---
        from app.models.communication import Attachment
        att_stmt = select(Attachment).where(
            Attachment.communication_id == message_id,
            Attachment.processing_status == "pending",
        )
        att_result = await session.execute(att_stmt)
        attachments = list(att_result.scalars().all())

        if attachments:
            logger.info(
                "[AIQueue Worker] Processing %d attachments for message %s",
                len(attachments), message_id_str,
            )
            await _process_attachments(session, attachments, comm.subject)
        
    finally:
        try:
            await session_gen.athrow(GeneratorExit)
        except Exception:
            pass


async def _process_attachments(
    session: AsyncSession,
    attachments: list,
    email_subject: str | None = None,
) -> None:
    """Process a list of Attachment records: extract text and generate AI summaries."""
    from app.services.attachment_extractor import AttachmentExtractor, MAX_AUTO_PROCESS_BYTES
    from app.providers.storage.local import LocalFileStorageProvider
    from app.ai.prompts.attachment_summarize import get_attachment_summarize_prompt
    from app.ai.prompts.vision_summarize import get_vision_summarize_prompt
    from app.ai.factory import AIProviderFactory

    extractor = AttachmentExtractor()
    storage = LocalFileStorageProvider()

    for att in attachments:
        try:
            # Skip large attachments
            if att.size_bytes and att.size_bytes > MAX_AUTO_PROCESS_BYTES:
                logger.info(
                    "[AIQueue Worker] Skipping large attachment '%s' (%d bytes > %d limit)",
                    att.name, att.size_bytes, MAX_AUTO_PROCESS_BYTES,
                )
                att.processing_status = "skipped"
                session.add(att)
                await session.commit()
                continue

            att.processing_status = "processing"
            session.add(att)
            await session.commit()

            # Load raw bytes from storage
            if not att.url:
                logger.warning("[AIQueue Worker] Attachment '%s' has no storage URL. Skipping.", att.name)
                att.processing_status = "failed"
                session.add(att)
                await session.commit()
                continue

            # Extract the storage path from the file:/// URL
            storage_path = att.url.replace("file:///", "").replace(storage.base_dir.as_posix() + "/", "")
            try:
                content_bytes = await storage.get_file(storage_path)
            except FileNotFoundError:
                logger.warning("[AIQueue Worker] Attachment file not found at '%s'. Skipping.", att.url)
                att.processing_status = "failed"
                session.add(att)
                await session.commit()
                continue

            # Determine category and extract text
            category = extractor.get_file_category(att.name, att.content_type)
            extracted = extractor.extract_text(att.name, content_bytes, att.content_type)

            if extracted:
                # Text-based: summarize via text LLM
                att.extracted_text = extracted
                provider = AIProviderFactory.get_provider()
                messages = get_attachment_summarize_prompt(att.name, extracted, email_subject)
                raw_summary = await provider.chat(messages)
                att.attachment_summary = raw_summary
                att.processing_status = "completed"
                logger.info("[AIQueue Worker] Text-based summary completed for '%s'", att.name)

            elif category == "image":
                # Image: use vision model
                import base64
                image_b64 = base64.b64encode(content_bytes).decode("utf-8")
                mime = att.content_type or "image/png"
                prompt = get_vision_summarize_prompt(att.name, email_subject)

                try:
                    provider = AIProviderFactory.get_provider()
                    if hasattr(provider, "vision_chat"):
                        raw_summary = await provider.vision_chat(prompt, image_b64, mime)
                        att.attachment_summary = raw_summary
                        att.processing_status = "completed"
                        logger.info("[AIQueue Worker] Vision summary completed for '%s'", att.name)
                    else:
                        logger.warning("[AIQueue Worker] Provider does not support vision. Skipping '%s'.", att.name)
                        att.processing_status = "skipped"
                except Exception as vision_err:
                    logger.error("[AIQueue Worker] Vision processing failed for '%s': %s", att.name, str(vision_err))
                    att.processing_status = "failed"
            else:
                logger.info("[AIQueue Worker] Unsupported attachment type for '%s'. Marking skipped.", att.name)
                att.processing_status = "skipped"

            session.add(att)
            await session.commit()

        except Exception as e:
            logger.exception("[AIQueue Worker] Failed to process attachment '%s': %s", att.name, str(e))
            att.processing_status = "failed"
            session.add(att)
            await session.commit()

