# app/modules/provider/models/education_model.py
from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProviderEducation(Base):
    __tablename__ = "provider_education"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    provider_profile_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("provider_profiles.id", ondelete="CASCADE"), nullable=False
    )

    degree: Mapped[str] = mapped_column(String(100), nullable=False)          # PhD, PsyD, LCSW, etc.
    institution: Mapped[str] = mapped_column(String(255), nullable=False)
    field_of_study: Mapped[str] = mapped_column(String(150), nullable=False)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    license_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    thesis_topic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    provider_profile: Mapped["ProviderProfile"] = relationship("ProviderProfile", back_populates="education")