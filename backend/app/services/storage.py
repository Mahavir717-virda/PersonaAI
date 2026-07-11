"""Storage Service implementation."""

import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.storage.base import StorageProvider
from app.providers.storage.local import LocalFileStorageProvider
from app.repositories.communication import CommunicationRepository
from app.models.communication import Attachment


class StorageService:
    """Orchestrates saving file attachments across storage engines and database logs."""

    def __init__(self, session: AsyncSession, provider: StorageProvider | None = None) -> None:
        self.session = session
        self._repo = CommunicationRepository(session)
        self.provider = provider or LocalFileStorageProvider()

    async def save_attachment(
        self, communication_id: uuid.UUID, filename: str, content: bytes, content_type: str | None = None
    ) -> Attachment:
        """Store attachment file to provider and register metadata record in database."""
        # Save payload to file engine
        file_url = await self.provider.save_file(f"{communication_id}/{filename}", content)

        # Create metadata ORM record
        attachment = Attachment(
            id=uuid.uuid4(),
            communication_id=communication_id,
            name=filename,
            content_type=content_type,
            url=file_url,
            size_bytes=len(content),
        )

        self.session.add(attachment)
        await self.session.commit()
        return attachment
