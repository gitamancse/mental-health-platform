# app/modules/provider/models/admin_action.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base
from enum import Enum as PyEnum

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ActionType(str, PyEnum):
    APPROVE_REGISTRATION = "approve_registration"
    REJECT_REGISTRATION = "reject_registration"
    MANUAL_NPI_OVERRIDE = "manual_npi_override"
    PUBLISH_PROFILE = "publish_profile"
    REQUEST_REVISIONS = "request_revisions"

class AdminAction(Base):
    __tablename__ = "admin_actions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )
    admin_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Renamed from 'metadata'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    admin: Mapped[Optional["User"]] = relationship("User", foreign_keys=[admin_id], back_populates="admin_actions_performed")
    target_user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id], back_populates="admin_actions_received")