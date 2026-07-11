"""Connector repository for SQL operations."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.communication import Connector, SyncCheckpoint, SyncHistory
from app.enums.platform import Platform
from app.enums.connector_state import ConnectorState


class ConnectorRepository:
    """Repository managing Connector, SyncCheckpoint, and SyncHistory DB models."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, connector_id: uuid.UUID) -> Optional[Connector]:
        """Fetch a connector configuration by UUID."""
        return await self.session.get(Connector, connector_id)

    async def list_by_user(self, user_id: uuid.UUID) -> List[Connector]:
        """List all connectors configured by a specific user."""
        stmt = select(Connector).where(Connector.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_platform_and_user(
        self, platform: Platform, user_id: uuid.UUID
    ) -> Optional[Connector]:
        """Fetch a connector config for a specific platform and user."""
        stmt = select(Connector).where(
            Connector.platform == platform, Connector.user_id == user_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_connector(
        self, user_id: uuid.UUID, platform: Platform, settings: Optional[dict] = None
    ) -> Connector:
        """Create a new connector configuration in disconnected state."""
        connector = Connector(
            user_id=user_id,
            platform=platform,
            state=ConnectorState.DISCONNECTED,
            settings=settings or {},
        )
        self.session.add(connector)
        await self.session.flush()
        return connector

    async def update_state(
        self, connector: Connector, state: ConnectorState
    ) -> Connector:
        """Update a connector's lifecycle state."""
        connector.state = state
        self.session.add(connector)
        await self.session.flush()
        return connector

    async def delete_connector(self, connector: Connector) -> None:
        """Remove a connector configuration."""
        await self.session.delete(connector)
        await self.session.flush()

    async def create_sync_history(self, connector_id: uuid.UUID) -> SyncHistory:
        """Log the start of a synchronization pass."""
        history = SyncHistory(
            connector_id=connector_id,
            started_at=datetime.now(timezone.utc),
            status="running",
        )
        self.session.add(history)
        await self.session.flush()
        return history

    async def update_sync_history(
        self,
        history: SyncHistory,
        status: str,
        messages_imported: int,
        attachments_imported: int,
        error: Optional[str] = None,
        failed_ids: Optional[List[str]] = None,
    ) -> SyncHistory:
        """Record the outcomes and durations of a completed sync pass."""
        history.status = status
        history.completed_at = datetime.now(timezone.utc)
        history.messages_imported = messages_imported
        history.attachments_imported = attachments_imported
        history.error = error
        history.failed_ids = failed_ids

        duration = (history.completed_at - history.started_at).total_seconds()
        history.duration = duration

        self.session.add(history)
        await self.session.flush()
        return history

    async def list_sync_history(
        self, connector_id: uuid.UUID, limit: int = 20
    ) -> List[SyncHistory]:
        """Fetch recent synchronization runs for a connector."""
        stmt = (
            select(SyncHistory)
            .where(SyncHistory.connector_id == connector_id)
            .order_by(SyncHistory.started_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_checkpoint(
        self, connector_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[SyncCheckpoint]:
        """Fetch the cursor checkpoint for synchronization indexing."""
        stmt = select(SyncCheckpoint).where(
            SyncCheckpoint.connector_id == connector_id,
            SyncCheckpoint.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_checkpoint(
        self, connector_id: uuid.UUID, user_id: uuid.UUID, cursor: Optional[str]
    ) -> SyncCheckpoint:
        """Create or update a cursor checkpoint."""
        checkpoint = await self.get_checkpoint(connector_id, user_id)
        if not checkpoint:
            checkpoint = SyncCheckpoint(
                connector_id=connector_id, user_id=user_id, cursor=cursor
            )
        else:
            checkpoint.cursor = cursor
        self.session.add(checkpoint)
        await self.session.flush()
        return checkpoint
