# app/modules/provider/models/provider_model.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, UniqueConstraint, ForeignKey, Enum, Text, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base
from app.modules.users.models.user_model import User

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ProviderProfile(Base):
    """Provider profile model for storing detailed information about mental health providers."""

    __tablename__ = "provider_profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Foreign key to users table
    # user_id: Mapped[UUID] = mapped_column(
    #     PG_UUID(as_uuid=True),
    #     ForeignKey("users.id", ondelete="CASCADE"),
    #     unique=True,
    #     nullable=False,
    #     index=True
    # )

    # Basic professional information
    professional_title: Mapped[str] = mapped_column(String(100), nullable=False)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Specializations and modalities
    specialties: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    modalities: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    languages: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Insurance and payment information
    insurance_accepted: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    session_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Location information
    office_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Website and online presence
    subdomain_slug: Mapped[Optional[str]] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )

    # Contact information
    phone_number_masked: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Client management
    accepting_new_clients: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    publish_requested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Ratings and reviews
    average_rating: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Subscription information
    subscription_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status tracking for admin governance
    status: Mapped[str] = mapped_column(
        String(20), default="draft", nullable=False, index=True
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # NPI information (required for US healthcare providers)
    npi_number: Mapped[Optional[str]] = mapped_column(String(10), unique=True, nullable=True)
    npi_validated: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    verified_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # Relationships
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="provider_profile", 
        foreign_keys=[user_id] 
    )
    # user: Mapped["User"] = relationship("User", back_populates="provider_profile")
    # licenses: Mapped[List["ProviderLicense"]] = relationship("ProviderLicense", back_populates="user")
    licenses: Mapped[List["ProviderLicense"]] = relationship(
        "ProviderLicense",
        primaryjoin="ProviderProfile.user_id == ProviderLicense.user_id",
        foreign_keys="[ProviderLicense.user_id]",
        viewonly=True  # Recommended because the 'User' model owns the data entry
    )
    # documents: Mapped[List["ProviderDocument"]] = relationship("ProviderDocument", back_populates="user")
    documents: Mapped[List["ProviderDocument"]] = relationship(
        "ProviderDocument",
        primaryjoin="ProviderProfile.user_id == ProviderDocument.user_id",
        foreign_keys="[ProviderDocument.user_id]",
        viewonly=True
    )
    subscriptions: Mapped[List["ProviderSubscription"]] = relationship("ProviderSubscription", back_populates="provider")

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

    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile", back_populates="subscriptions")

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
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    
    license_number: Mapped[str] = mapped_column(String(100), nullable=False)
    license_type: Mapped[str] = mapped_column(String(50), nullable=False) 
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    expiry_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="pending") 
    admin_proof_url: Mapped[Optional[str]] = mapped_column(String(500))
    
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    verified_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"))
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    # Relationship back to User
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="licenses",
        # Explicitly tell SQLAlchemy to use the 'user_id' column here too
        foreign_keys=[user_id] 
    )
    
    # Optional: If you want a relationship for the admin who verified it
    verified_by_admin: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[verified_by]
    )
    __table_args__ = (
        UniqueConstraint('user_id', 'state', 'license_number', name='_user_license_uc'),
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
