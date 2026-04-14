# app/modules/provider/models/provider_registration.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base
from enum import Enum as PyEnum

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

# Define the enum as a Python enum
class RegistrationStatus(str, PyEnum):
    PENDING_NPI_VALIDATION = "pending_npi_validation"
    PENDING_ADMIN_REVIEW = "pending_admin_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUEST_REVISIONS = "request_revisions"

    @classmethod
    def values(cls):
        return [item.value for item in cls]

class ProviderRegistration(Base):
    __tablename__ = "provider_registrations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4, index=True
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False, index=True
    )

    # Personal Info
    # title: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    # first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    # email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # # Address Info
    # address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    # address_line2: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # city: Mapped[str] = mapped_column(String(100), nullable=False)
    # postcode: Mapped[str] = mapped_column(String(20), nullable=False)
    # country: Mapped[str] = mapped_column(String(50), default="US", nullable=False)    
    
    # # Professional Info
    # professional_role: Mapped[str] = mapped_column(String(50), nullable=False)
    # academic_degree: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # # Licensing Board Info
    # licensing_board: Mapped[str] = mapped_column(String(255), nullable=False)
    # registry_id: Mapped[str] = mapped_column(String(100), nullable=False) # "Name or ID in Registry"
    # membership_type: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # # NPI/License Info
    # npi_number: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    # npi_validated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # admin_override: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # override_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # license_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # license_state: Mapped[str] = mapped_column(String(2), nullable=False)
    # license_proof_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # # Generic Billing Fields
    # billing_customer_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # billing_subscription_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # billing_status: Mapped[Optional[str]] = mapped_column(String(50), default="trialing")
    
    # # Workflow Status - FIXED: Use String type with Enum values
    # status: Mapped[str] = mapped_column(
    #     String(50),  # Use String type instead of Enum
    #     default=RegistrationStatus.PENDING_ADMIN_REVIEW.value,
    #     nullable=False, index=True
    # )

    # admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # rejection_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # # Timestamps
    # submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    
    title: Mapped[str] = mapped_column(String(20))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    
    address: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(2))
    city: Mapped[str] = mapped_column(String(100))
    zip_code: Mapped[str] = mapped_column(String(20))
    
    academic_degree: Mapped[str] = mapped_column(String(50))
    npi_type: Mapped[str] = mapped_column(String(20))
    npi_number: Mapped[str] = mapped_column(String(10), unique=True)
    
    # Keep these for the workflow
    npi_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(50), default=RegistrationStatus.PENDING_ADMIN_REVIEW.value)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    
    reviewed_by: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    # The owner of the registration
    user: Mapped["User"] = relationship(
        "User", 
        back_populates="provider_registration", 
        foreign_keys=[user_id] 
    )

    # The admin who reviewed it
    reviewed_by_user: Mapped[Optional["User"]] = relationship(
        "User", 
        foreign_keys=[reviewed_by] # <--- ADD THIS
    )