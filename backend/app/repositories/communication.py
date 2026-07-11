"""Communication repository for SQL operations."""

import uuid
from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import select, and_, or_, desc, func, not_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.communication import (
    Communication,
    Conversation,
    Participant,
    Attachment,
    Connector,
)
from app.enums.platform import Platform
from app.enums.communication_status import CommunicationStatus


class CommunicationRepository:
    """Repository managing communications, conversations, participants, and attachments."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, communication_id: uuid.UUID) -> Optional[Communication]:
        """Fetch a communication with related attachments and participants loaded."""
        stmt = (
            select(Communication)
            .where(Communication.id == communication_id)
            .options(
                selectinload(Communication.participants),
                selectinload(Communication.attachments),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_platform_message_id(
        self,
        platform: Platform,
        platform_message_id: str,
        connector_id: uuid.UUID | None = None,
    ) -> Optional[Communication]:
        """Fetch a communication by its platform-specific message ID."""
        stmt = select(Communication).where(
            Communication.platform == platform,
            Communication.platform_message_id == platform_message_id,
        ).options(
            selectinload(Communication.participants),
            selectinload(Communication.attachments),
        )
        if connector_id is not None:
            stmt = stmt.where(Communication.connector_id == connector_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_communications(
        self,
        user_id: uuid.UUID,
        platform: Optional[Platform] = None,
        status: Optional[CommunicationStatus] = None,
        exclude_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Communication]:
        """List communications belonging to a user, optionally filtered by platform or status."""
        stmt = (
            select(Communication)
            .join(Connector, Connector.id == Communication.connector_id)
            .where(Connector.user_id == user_id)
            .options(
                selectinload(Communication.participants),
                selectinload(Communication.attachments),
            )
            .order_by(desc(Communication.created_at))
            .limit(limit)
            .offset(offset)
        )

        if platform:
            stmt = stmt.where(Communication.platform == platform)
        if status:
            stmt = stmt.where(Communication.status == status)
        if exclude_query:
            exclusion = self._build_exclusion_clause(exclude_query)
            stmt = stmt.where(~exclusion)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search_communications(
        self,
        user_id: uuid.UUID,
        query: Optional[str] = None,
        platform: Optional[Platform] = None,
        sender: Optional[str] = None,
        subject: Optional[str] = None,
        exclude_query: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Communication]:
        """Query messages using keyword matching on sender, subject, and body text."""
        stmt = (
            select(Communication)
            .join(Connector, Connector.id == Communication.connector_id)
            .where(Connector.user_id == user_id)
            .options(
                selectinload(Communication.participants),
                selectinload(Communication.attachments),
            )
            .order_by(desc(Communication.created_at))
            .limit(limit)
            .offset(offset)
        )

        # Filters
        if platform:
            stmt = stmt.where(Communication.platform == platform)
        if start_date:
            stmt = stmt.where(Communication.created_at >= start_date)
        if end_date:
            stmt = stmt.where(Communication.created_at <= end_date)
        if subject:
            stmt = stmt.where(Communication.subject.ilike(f"%{subject}%"))

        # Keyword Search (sender name/address, subject, or message body)
        if query:
            search_filters = [
                Communication.subject.ilike(f"%{query}%"),
                Communication.body.ilike(f"%{query}%"),
            ]

            # Subquery or join for participant addresses/names
            p_stmt = select(Participant.communication_id).where(
                or_(
                    Participant.name.ilike(f"%{query}%"),
                    Participant.address.ilike(f"%{query}%"),
                )
            )
            stmt = stmt.where(or_(*search_filters, Communication.id.in_(p_stmt)))

        if sender:
            sender_stmt = select(Participant.communication_id).where(
                and_(
                    Participant.type == "sender",
                    or_(
                        Participant.name.ilike(f"%{sender}%"),
                        Participant.address.ilike(f"%{sender}%"),
                    ),
                )
            )
            stmt = stmt.where(Communication.id.in_(sender_stmt))

        if exclude_query:
            stmt = stmt.where(~self._build_exclusion_clause(exclude_query))

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _build_exclusion_clause(self, exclude_query: str):
        """Create a SQLAlchemy exclusion clause for matching subject/body/sender content."""
        pattern = f"%{exclude_query}%"
        sender_stmt = select(Participant.communication_id).where(
            and_(
                Participant.type == "sender",
                or_(
                    Participant.name.ilike(pattern), Participant.address.ilike(pattern)
                ),
            )
        )
        return or_(
            Communication.subject.ilike(pattern),
            Communication.body.ilike(pattern),
            Communication.id.in_(sender_stmt),
        )

    async def get_recent(
        self, user_id: uuid.UUID, limit: int = 5
    ) -> List[Communication]:
        """Fetch the most recent communications for a quick preview list."""
        return await self.list_communications(user_id=user_id, limit=limit)

    async def get_summary_stats(self, user_id: uuid.UUID) -> dict:
        """Fetch general message counts for platform dashboard panels."""
        stmt = (
            select(Communication.platform, func.count(Communication.id))
            .join(Connector, Connector.id == Communication.connector_id)
            .where(Connector.user_id == user_id)
            .group_by(Communication.platform)
        )
        result = await self.session.execute(stmt)
        stats = {
            (
                row[0].name.lower() if hasattr(row[0], "name") else str(row[0]).lower()
            ): row[1]
            for row in result.all()
        }

        # Add totals
        total = sum(stats.values())
        stats["total"] = total
        return stats

    async def get_or_create_conversation(
        self, platform: Platform, platform_conversation_id: str
    ) -> Conversation:
        """Fetch an existing thread or create a new one."""
        stmt = select(Conversation).where(
            Conversation.platform == platform,
            Conversation.platform_conversation_id == platform_conversation_id,
        )
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()

        if not conversation:
            conversation = Conversation(
                platform=platform, platform_conversation_id=platform_conversation_id
            )
            self.session.add(conversation)
            await self.session.flush()

        return conversation

    async def list_conversations(
        self, user_id: uuid.UUID, limit: int = 20, offset: int = 0
    ) -> List[Conversation]:
        """List thread conversations."""
        # Simple query for conversations containing user communications
        stmt = (
            select(Conversation)
            .join(Communication, Communication.conversation_id == Conversation.id)
            .join(Connector, Connector.id == Communication.connector_id)
            .where(Connector.user_id == user_id)
            .distinct()
            .order_by(desc(Conversation.created_at))
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_communication(self, communication: Communication) -> Communication:
        """Persist a normalized communication record."""
        self.session.add(communication)
        await self.session.flush()
        return communication
