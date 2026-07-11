"""Connector service implementation."""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.connector import ConnectorRepository
from app.connectors import connector_manager
from app.enums.platform import Platform
from app.enums.connector_state import ConnectorState
from app.exceptions.authentication import AuthenticationError


class ConnectorService:
    """Service layer managing connector accounts, credentials, and health states."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._repo = ConnectorRepository(session)

    async def list_available_connectors(self) -> List[dict]:
        """List manifests for all registered third-party platforms."""
        return connector_manager.get_available_manifests()

    async def list_user_connectors(self, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """List active user connector integrations along with status metadata."""
        db_connectors = await self._repo.list_by_user(user_id)
        available = connector_manager.get_available_manifests()
        available_map = {m["id"]: m for m in available}

        connectors_list = []
        for conn in db_connectors:
            platform_str = conn.platform.name.lower()
            manifest = available_map.get(platform_str, {})
            
            # Retrieve recent sync history
            histories = await self._repo.list_sync_history(conn.id, limit=1)
            last_sync_time = histories[0].completed_at.isoformat() if histories and histories[0].completed_at else None
            last_sync_status = histories[0].status if histories else "never"

            connectors_list.append({
                "id": str(conn.id),
                "platform": platform_str,
                "name": manifest.get("name", conn.platform.name),
                "state": conn.state.value,
                "settings": conn.settings or {},
                "last_sync": last_sync_time,
                "last_sync_status": last_sync_status,
                "icon": manifest.get("icon", ""),
                "capabilities": manifest.get("capabilities", {}),
            })

        return connectors_list

    async def connect_platform(
        self, user_id: uuid.UUID, platform_str: str, auth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure credentials and activate a platform integration."""
        if platform_str.lower() == "gmail":
            raise ValueError("This endpoint is deprecated. Use GET /api/v1/connectors/gmail/auth-url instead.")
        try:
            platform = Platform[platform_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid platform specified: '{platform_str}'")

        # Get or create DB connector config
        connector = await self._repo.get_by_platform_and_user(platform, user_id)
        if not connector:
            connector = await self._repo.create_connector(user_id, platform)

        # Update to AUTHORIZING
        await self._repo.update_state(connector, ConnectorState.AUTHORIZING)
        await self.session.commit()

        try:
            # Instantiate connector and perform authorization flow
            client = await connector_manager.get_connector(
                str(connector.id), platform_str, {}
            )
            credentials = await client.authorize(auth_data)

            # Store credentials securely encrypted using CredentialManager
            from app.services.credential_manager import CredentialManager
            cm = CredentialManager()
            encrypted_creds = cm.encrypt_credentials(credentials)

            updated_settings = {
                **(connector.settings or {}),
                "credentials": encrypted_creds,
            }
            connector.settings = updated_settings
            await self._repo.update_state(connector, ConnectorState.CONNECTED)
            await self.session.commit()

            return {
                "id": str(connector.id),
                "platform": platform_str,
                "state": connector.state.value,
            }
        except Exception as e:
            await self._repo.update_state(connector, ConnectorState.ERROR)
            await self.session.commit()
            raise RuntimeError(f"Connection flow failed: {str(e)}")

    async def disconnect_platform(self, user_id: uuid.UUID, platform_str: str) -> None:
        """Revoke credentials and remove a platform integration."""
        try:
            platform = Platform[platform_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid platform: '{platform_str}'")

        connector = await self._repo.get_by_platform_and_user(platform, user_id)
        if not connector:
            raise ValueError("Connector integration not found")

        # Disconnect client
        await connector_manager.disconnect_connector(str(connector.id), platform_str)

        # Delete database config
        await self._repo.delete_connector(connector)
        await self.session.commit()

    async def check_health(self, user_id: uuid.UUID, platform_str: str) -> bool:
        """Check provider connection status and credentials validity."""
        try:
            platform = Platform[platform_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid platform: '{platform_str}'")

        connector = await self._repo.get_by_platform_and_user(platform, user_id)
        if not connector:
            return False

        encrypted_creds = (connector.settings or {}).get("credentials", {})
        if isinstance(encrypted_creds, str):
            from app.services.credential_manager import CredentialManager
            cm = CredentialManager()
            credentials = cm.decrypt_credentials(encrypted_creds)
        else:
            credentials = encrypted_creds or {}

        try:
            client = await connector_manager.get_connector(
                str(connector.id), platform_str, credentials
            )
            is_healthy = await client.health()
            if not is_healthy:
                await self._repo.update_state(connector, ConnectorState.RECONNECT_REQUIRED)
                await self.session.commit()
            return is_healthy
        except Exception:
            await self._repo.update_state(connector, ConnectorState.ERROR)
            await self.session.commit()
            return False

    async def get_metrics(self, user_id: uuid.UUID) -> Dict[str, Any]:
        """Aggregate data metrics for user connectors."""
        connectors = await self._repo.list_by_user(user_id)
        connected_count = sum(1 for c in connectors if c.state == ConnectorState.CONNECTED)
        
        # Calculate totals from sync histories
        total_syncs = 0
        total_imported = 0
        durations = []
        failed_syncs = 0

        for conn in connectors:
            runs = await self._repo.list_sync_history(conn.id, limit=50)
            total_syncs += len(runs)
            for r in runs:
                total_imported += r.messages_imported
                if r.status == "failed":
                    failed_syncs += 1
                if r.duration is not None:
                    durations.append(r.duration)

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "connected_accounts": connected_count,
            "total_syncs": total_syncs,
            "failed_syncs": failed_syncs,
            "messages_imported": total_imported,
            "avg_sync_time_seconds": round(avg_duration, 2),
        }
