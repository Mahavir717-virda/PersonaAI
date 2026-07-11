"""Communication service implementation."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.communication import CommunicationRepository
from app.models.communication import Communication
from app.enums.platform import Platform
from app.enums.communication_status import CommunicationStatus


class CommunicationService:
    """Service layer managing communications retrieval, searching, and preview summaries."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._repo = CommunicationRepository(session)

    async def list_communications(
        self,
        user_id: uuid.UUID,
        platform_str: Optional[str] = None,
        status_str: Optional[str] = None,
        exclude_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List communications with structured serialization for responses."""
        platform = None
        if platform_str:
            try:
                platform = Platform[platform_str.upper()]
            except KeyError:
                raise ValueError(f"Invalid platform: '{platform_str}'")

        status = None
        if status_str:
            try:
                status = CommunicationStatus[status_str.upper()]
            except KeyError:
                raise ValueError(f"Invalid status: '{status_str}'")

        records = await self._repo.list_communications(
            user_id=user_id,
            platform=platform,
            status=status,
            exclude_query=exclude_query,
            limit=limit,
            offset=offset,
        )
        return [self._serialize(r) for r in records]

    async def get_communication_detail(
        self, user_id: uuid.UUID, communication_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """Fetch a specific communication details."""
        record = await self._repo.get_by_id(communication_id)
        if not record:
            return None

        # Verify ownership via connector
        if record.connector and record.connector.user_id != user_id:
            raise PermissionError("Access denied to this communication resource")

        return self._serialize(record)

    async def search_communications(
        self,
        user_id: uuid.UUID,
        query: Optional[str] = None,
        platform_str: Optional[str] = None,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        exclude_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Perform keyword search queries against subjects, bodies, and sender credentials."""
        platform = None
        if platform_str:
            try:
                platform = Platform[platform_str.upper()]
            except KeyError:
                raise ValueError(f"Invalid platform: '{platform_str}'")

        records = await self._repo.search_communications(
            user_id=user_id,
            query=query,
            platform=platform,
            sender=sender,
            subject=subject,
            exclude_query=exclude_query,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
        )
        return [self._serialize(r) for r in records]

    async def get_recent(
        self, user_id: uuid.UUID, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """List recent communications."""
        records = await self._repo.get_recent(user_id=user_id, limit=limit)
        return [self._serialize(r) for r in records]

    async def get_summary(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Aggregate message counts for active platforms."""
        return await self._repo.get_summary_stats(user_id=user_id)

    def _serialize(self, comm: Communication) -> Dict[str, Any]:
        """Convert Communication ORM record to a standard dict response shape."""
        # Find sender
        sender = next((p for p in comm.participants if p.type == "sender"), None)
        receivers = [p.address for p in comm.participants if p.type == "recipient"]

        return {
            "id": str(comm.id),
            "platform": comm.platform.name.lower(),
            "platform_message_id": comm.platform_message_id,
            "subject": comm.subject,
            "body": comm.body,
            "html_body": comm.html_body,
            "status": comm.status.value,
            "importance": comm.importance,
            "created_at": comm.created_at.isoformat(),
            "sender_name": sender.name if sender else "Unknown",
            "sender_address": sender.address if sender else "",
            "receivers": receivers,
            "attachments": [
                {
                    "id": str(att.id),
                    "name": att.name,
                    "content_type": att.content_type,
                    "url": att.url,
                    "size_bytes": att.size_bytes,
                }
                for att in comm.attachments
            ],
            "metadata": comm.metadata_fields or {},
        }
