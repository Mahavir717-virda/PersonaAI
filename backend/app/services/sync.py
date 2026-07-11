"""Sync service implementation."""

import logging
import uuid
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.connector import ConnectorRepository
from app.connectors import connector_manager
from app.enums.platform import Platform
from app.enums.connector_state import ConnectorState
from app.services.pipeline import CommunicationPipeline

logger = logging.getLogger(__name__)


class SyncService:
    """Service layer managing platform synchronization cycles, checkpoints, and histories."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._connector_repo = ConnectorRepository(session)
        self.pipeline = CommunicationPipeline(session)

    async def trigger_sync(self, user_id: uuid.UUID, platform_str: str) -> dict:
        """Execute a synchronization cycle for a platform connector."""
        try:
            platform = Platform[platform_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid platform: '{platform_str}'")

        connector = await self._connector_repo.get_by_platform_and_user(platform, user_id)
        if not connector:
            raise ValueError("Connector integration not found for user")

        if connector.state == ConnectorState.SYNCING:
            return {"status": "already_syncing"}

        # Start logging sync history run
        history = await self._connector_repo.create_sync_history(connector.id)
        await self._connector_repo.update_state(connector, ConnectorState.SYNCING)
        await self.session.commit()

        messages_imported = 0
        attachments_imported = 0
        error_msg = None

        try:
            logger.info("[SyncService] Starting sync for user %s on %s", user_id, platform_str)
            encrypted_creds = (connector.settings or {}).get("credentials", {})
            if isinstance(encrypted_creds, str):
                from app.services.credential_manager import CredentialManager
                cm = CredentialManager()
                credentials = cm.decrypt_credentials(encrypted_creds)
            else:
                credentials = encrypted_creds or {}

            logger.info("[SyncService] Building connector client for connector %s", connector.id)
            client = await connector_manager.get_connector(
                str(connector.id), platform_str, credentials
            )

            # Get latest cursor checkpoint
            logger.info("[SyncService] Loading checkpoint for connector %s", connector.id)
            checkpoint = await self._connector_repo.get_checkpoint(connector.id, user_id)
            cursor = checkpoint.cursor if checkpoint else None

            # Sync loop
            new_cursor = None
            try:
                logger.info(
                    "[SyncService] Beginning message stream for connector %s from cursor %s",
                    connector.id,
                    cursor,
                )
                async for raw_record in client.sync(cursor):
                    record_id = raw_record.get("id")
                    logger.info("[SyncService] Ingesting message %s", record_id)
                    # Route through central communication pipeline
                    result = await self.pipeline.process_payload(
                        platform_str,
                        raw_record,
                        connector_id=connector.id,
                    )
                    if result and result.is_new:
                        messages_imported += 1
                        attachments_imported += result.attachment_count
                    
                    # Update checkpoint cursor tracker when the connector exposes a checkpoint
                    new_cursor = getattr(client, "last_sync_cursor", None) or new_cursor
                new_cursor = getattr(client, "last_sync_cursor", None) or new_cursor
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    logger.info("[SyncService] Access token expired (HTTP 401). Refreshing token...")
                    # Refresh credentials
                    new_creds = await client.refresh_credentials(credentials)
                    
                    # Encrypt and save back to database
                    from app.services.credential_manager import CredentialManager
                    cm = CredentialManager()
                    encrypted_new = cm.encrypt_credentials(new_creds)
                    
                    connector.settings = {
                        **(connector.settings or {}),
                        "credentials": encrypted_new,
                    }
                    await self.session.commit()

                    # Update client in-memory credentials
                    await client.connect(new_creds)

                    # Retry synchronization pass
                    logger.info("[SyncService] Retrying sync after credential refresh")
                    async for raw_record in client.sync(cursor):
                        result = await self.pipeline.process_payload(
                            platform_str,
                            raw_record,
                            connector_id=connector.id,
                        )
                        if result and result.is_new:
                            messages_imported += 1
                            attachments_imported += result.attachment_count
                        new_cursor = getattr(client, "last_sync_cursor", None) or new_cursor
                    new_cursor = getattr(client, "last_sync_cursor", None) or new_cursor
                else:
                    raise e

            # Save checkpoint cursor state
            if new_cursor:
                await self._connector_repo.update_checkpoint(connector.id, user_id, new_cursor)

            failed_ids = client.get_failed_ids()
            status = "success"
            if failed_ids:
                status = "partial_success"
                error_msg = f"{len(failed_ids)} messages failed to sync."

            # Update history log
            await self._connector_repo.update_sync_history(
                history,
                status=status,
                messages_imported=messages_imported,
                attachments_imported=attachments_imported,
                failed_ids=failed_ids,
                error=error_msg,
            )
            await self._connector_repo.update_state(connector, ConnectorState.CONNECTED)
            await self.session.commit()

        except Exception as e:
            logger.error(f"Sync pass failed for user {user_id} on {platform_str}: {str(e)}", exc_info=True)
            error_msg = str(e)
            await self._connector_repo.update_sync_history(
                history,
                status="failed",
                messages_imported=messages_imported,
                attachments_imported=attachments_imported,
                error=error_msg,
            )
            await self._connector_repo.update_state(connector, ConnectorState.ERROR)
            await self.session.commit()

        return {
            "status": "success" if not error_msg else "failed",
            "messages_imported": messages_imported,
            "attachments_imported": attachments_imported,
            "error": error_msg,
        }
