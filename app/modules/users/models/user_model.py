# app/modules/users/models/user_model.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List

import enum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text, JSON, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    EXECUTIVE = "executive"
    PROVIDER = "provider"
    CLIENT = "client"


class AccountStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, values_callable=lambda x: [e.value for e in x], native_enum=True, name="userrole"),
        nullable=False,
        index=True,
    )
    account_status: Mapped[AccountStatus] = mapped_column(
        Enum(
            AccountStatus,
            values_callable=lambda x: [e.value for e in x],
            native_enum=True,
            name="accountstatus",
        ),
        default=AccountStatus.PENDING,
        nullable=False,
        index=True,
    )

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    mfa_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    verification_code: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    verification_code_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_reset_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_reset_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_password_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Multi-tenancy foundation
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    provider_profile: Mapped[Optional["ProviderProfile"]] = relationship(
        "ProviderProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    client_profile: Mapped[Optional["ClientProfile"]] = relationship(
        "ClientProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    admin_profile: Mapped[Optional["AdminProfile"]] = relationship(
        "AdminProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    executive_profile: Mapped[Optional["ExecutiveProfile"]] = relationship(
        "ExecutiveProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    organization_members: Mapped[List["OrganizationMember"]] = relationship(
        "OrganizationMember", back_populates="user", cascade="all, delete-orphan"
    )

    licenses: Mapped[List["ProviderLicense"]] = relationship(
        "ProviderLicense",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="ProviderLicense.user_id",
    )
    documents: Mapped[List["ProviderDocument"]] = relationship(
        "ProviderDocument", back_populates="user", cascade="all, delete-orphan"
    )

    provider_registration: Mapped[Optional["ProviderRegistration"]] = relationship(
        "ProviderRegistration",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        foreign_keys="ProviderRegistration.user_id"
    )

    admin_actions_performed: Mapped[List["AdminAction"]] = relationship(
        "AdminAction", back_populates="admin", foreign_keys="AdminAction.admin_id"
    )
    admin_actions_received: Mapped[List["AdminAction"]] = relationship(
        "AdminAction", back_populates="target_user", foreign_keys="AdminAction.user_id"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"


class AdminProfile(Base):
    __tablename__ = "admin_profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    admin_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_admin_activity_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Added as requested
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="admin_profile")


class ExecutiveProfile(Base):
    __tablename__ = "executive_profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    executive_title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    organization_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    permissions: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Added as requested
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="executive_profile")


class ProviderProfile(Base):
    __tablename__ = "provider_profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    professional_title: Mapped[str] = mapped_column(String(100), nullable=False)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    specialties: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    modalities: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    languages: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    insurance_accepted: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    office_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    subdomain_slug: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)

    phone_number_masked: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    accepting_new_clients: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    publish_requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    profile_status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False) # draft, pending, published
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    average_rating: Mapped[Optional[float]] = mapped_column(Float, default=0.0, nullable=True)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    subscription_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Added as requested
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="provider_profile")

    education: Mapped[list["ProviderEducation"]] = relationship(
        "ProviderEducation",
        back_populates="provider_profile",
        cascade="all, delete-orphan"
    )


class ClientProfile(Base):
    __tablename__ = "client_profiles"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    date_of_birth: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pronouns: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    preferred_language: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    self_assessment_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    subscription_tier: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    membership_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    referral_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    total_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Added as requested
    profile_picture_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="client_profile")

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
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped["User"] = relationship(
        "User",
        back_populates="licenses",
        foreign_keys=[user_id],
    )

    verified_by_user: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[verified_by],
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

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    performed_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[user_id])


class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    performed_by_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    performed_by: Mapped["User"] = relationship("User", foreign_keys=[performed_by_id])
