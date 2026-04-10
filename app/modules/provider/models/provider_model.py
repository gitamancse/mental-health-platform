from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base
from app.modules.users.models.user_model import User

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class ProviderProfile(Base):
    """Provider profile model for storing detailed information about mental health providers."""

    __tablename__ = "provider_profiles"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )

    # Foreign key to users table
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

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

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="provider_profile"
    )

    # Additional relationships would be defined in separate model files
    # licenses: relationship to ProviderLicense
    # documents: relationship to ProviderDocument
    # subscriptions: relationship to ProviderSubscription
    # education: relationship to ProviderEducation