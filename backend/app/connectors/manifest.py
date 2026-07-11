"""Connector manifest metadata definition."""

from pydantic import BaseModel, Field


class ConnectorCapabilities(BaseModel):
    """Flags describing what functional capabilities a platform connector supports."""

    supports_search: bool = True
    supports_labels: bool = True
    supports_attachments: bool = True
    supports_threads: bool = True
    supports_push: bool = False
    supports_streaming: bool = False
    supports_drafts: bool = False


class ConnectorManifest(BaseModel):
    """Metadata describing a platform connector to register/render dynamically in the UI."""

    id: str
    name: str
    version: str = "1.0.0"
    supports_oauth: bool = True
    supports_webhooks: bool = False
    supports_sync: bool = True
    required_scopes: list[str] = Field(default_factory=list)
    icon: str = ""  # Base64 SVG or friendly Lucide icon identifier
    capabilities: ConnectorCapabilities = Field(default_factory=ConnectorCapabilities)
