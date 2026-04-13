# app/modules/client/models/client_model.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional, List

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Integer, Float, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from app.modules.users.models.user_model import ClientProfile
from app.modules.users.models.user_model import ProviderProfile

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ClientSubscription(Base):
    __tablename__ = "client_subscriptions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    plan_name: Mapped[str] = mapped_column(String(100), nullable=False)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    expiry_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientIntakeForm(Base):
    __tablename__ = "client_intake_forms"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    form_type: Mapped[str] = mapped_column(String(100), nullable=False)
    responses: Mapped[dict] = mapped_column(JSON, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientAssessment(Base):
    __tablename__ = "client_assessments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    assessment_type: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    responses: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    taken_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientConsent(Base):
    __tablename__ = "client_consents"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    consent_type: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    accepted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientPreference(Base):
    __tablename__ = "client_preferences"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    notification_email: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_sms: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_push: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_language: Mapped[str] = mapped_column(String(50), default="en", nullable=False)
    preferred_modality: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    custom_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")

class ClientMedicalHistory(Base):
    __tablename__ = "client_medical_history"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    conditions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    medications: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    allergies: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientTherapySession(Base):
    __tablename__ = "client_therapy_sessions"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id"), nullable=False
    )
    appointment_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    session_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")
    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")


class ClientNote(Base):
    __tablename__ = "client_notes"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientGoal(Base):
    __tablename__ = "client_goals"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="IN_PROGRESS", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientProgress(Base):
    __tablename__ = "client_progress"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    goal_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("client_goals.id"), nullable=True)
    progress_percentage: Mapped[float] = mapped_column(Float, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientJournalEntry(Base):
    __tablename__ = "client_journal_entries"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    mood_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-10
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientAppointment(Base):
    __tablename__ = "client_appointments"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    provider_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id"), nullable=False
    )
    appointment_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")
    provider: Mapped["ProviderProfile"] = relationship("ProviderProfile")


class ClientMedication(Base):
    __tablename__ = "client_medications"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str] = mapped_column(String(100), nullable=True)
    prescribed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientAllergy(Base):
    __tablename__ = "client_allergies"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    allergen: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=True)  # Mild, Moderate, Severe
    reaction: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    noted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")


class ClientDocument(Base):
    __tablename__ = "client_documents"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    client_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("client_profiles.id", ondelete="CASCADE"), nullable=False
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    client: Mapped["ClientProfile"] = relationship("ClientProfile")