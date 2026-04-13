# app/modules/organizations/models/organization_model.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List
import enum
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class OrgType(str, enum.Enum):
    CLINIC = "clinic"
    GROUP_PRACTICE = "group_practice"
    HOSPITAL = "hospital"
    PRIVATE_PRACTICE = "private_practice"


class OrgStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    address_line1: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[OrgStatus] = mapped_column(
        Enum(OrgStatus, native_enum=True, name="orgstatus"),
        default=OrgStatus.PENDING,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    members: Mapped[List["OrganizationMember"]] = relationship("OrganizationMember", back_populates="organization", cascade="all, delete-orphan")
    settings: Mapped["OrganizationSetting"] = relationship("OrganizationSetting", back_populates="organization", uselist=False, cascade="all, delete-orphan")
    billing_info: Mapped["OrganizationBillingInfo"] = relationship("OrganizationBillingInfo", back_populates="organization", uselist=False, cascade="all, delete-orphan")


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role_in_org: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "owner", "manager", "staff"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="organization_members")


class OrganizationSetting(Base):
    __tablename__ = "organization_settings"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    default_session_duration: Mapped[int] = mapped_column(Integer, default=60, nullable=False)  # minutes
    allow_self_booking: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    require_approval_for_new_clients: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    custom_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="settings")


class OrganizationBillingInfo(Base):
    __tablename__ = "organization_billing_info"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    stripe_connect_account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    billing_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="billing_info")


class OrganizationInvite(Base):
    __tablename__ = "organization_invites"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    invited_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role_in_org: Mapped[str] = mapped_column(String(50), nullable=False)
    token: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    organization: Mapped["Organization"] = relationship("Organization")


class OrganizationBranding(Base):
    __tablename__ = "organization_branding"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    primary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    secondary_color: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    favicon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)

    organization: Mapped["Organization"] = relationship("Organization")