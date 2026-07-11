"""Communication account database model."""

import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.enums.platform import Platform
from app.models.user import TimestampMixin


class CommunicationAccount(Base, TimestampMixin):
    """User communication channel accounts (Gmail, WhatsApp, Slack)."""

    __tablename__ = "communication_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    platform: Mapped[Platform] = mapped_column(SQLEnum(Platform), nullable=False)
    identifier: Mapped[str] = mapped_column(String(255), nullable=False) # e.g. email or phone
    is_connected: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User")
