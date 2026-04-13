# app/modules/provider/models/provider_model.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Float, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProviderAvailability(Base):
    __tablename__ = "provider_availabilities"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Sunday ... 6=Saturday
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)   # "09:00"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")


class ProviderBlockedTime(Base):
    __tablename__ = "provider_blocked_times"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False
    )
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")


class ProviderReview(Base):
    __tablename__ = "provider_reviews"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    session_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")
    client: Mapped["User"] = relationship("User")


class ProviderSubscription(Base):
    __tablename__ = "provider_subscriptions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False
    )
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    current_period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    current_period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")


class ProviderPublicationRequest(Base):
    __tablename__ = "provider_publication_requests"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING", nullable=False)  # PENDING, APPROVED, REJECTED
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewer_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")


class ProviderGallery(Base):
    __tablename__ = "provider_gallery"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")


class ProviderWaitlist(Base):
    __tablename__ = "provider_waitlist"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False
    )
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")
    client: Mapped["User"] = relationship("User")


class ProviderLicense(Base):
    __tablename__ = "provider_licenses"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    license_number: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped["User"] = relationship(
        "User", back_populates="licenses", foreign_keys=[user_id]
    )
    verified_by_user: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[verified_by]
    )


class ProviderDocument(Base):
    __tablename__ = "provider_documents"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="documents")