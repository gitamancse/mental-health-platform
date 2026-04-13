# app/modules/executive/models/executive_model.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExecutivePermission(Base):
    __tablename__ = "executive_permissions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    executive_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("executive_profiles.id", ondelete="CASCADE"), nullable=False
    )
    permission: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "provider_onboarding", "billing_view"
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    executive: Mapped["ExecutiveProfile"] = relationship("ExecutiveProfile")


class ExecutiveActivityLog(Base):
    __tablename__ = "executive_activity_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    executive_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("executive_profiles.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    executive: Mapped["ExecutiveProfile"] = relationship("ExecutiveProfile")


class ClinicStaff(Base):
    __tablename__ = "clinic_staff"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(100), nullable=False)  # receptionist, billing specialist, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    hired_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship("Organization")
    user: Mapped["User"] = relationship("User")


class ClinicAnnouncement(Base):
    __tablename__ = "clinic_announcements"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="normal", nullable=False)  # normal, high, urgent
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization")