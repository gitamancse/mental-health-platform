# app/modules/provider/schemas/provider_schema.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, HttpUrl

from app.modules.users.schemas.user_schema import ProviderProfileResponse


# ====================== AVAILABILITY ======================
class ProviderAvailabilityResponse(BaseModel):
    id: UUID
    day_of_week: int
    start_time: str
    end_time: str
    is_recurring: bool

    model_config = ConfigDict(from_attributes=True)


class ProviderAvailabilityCreateRequest(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: str = Field(..., pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    is_recurring: bool = True

    model_config = ConfigDict(extra="forbid")


class ProviderAvailabilityUpdateRequest(BaseModel):
    start_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    end_time: Optional[str] = Field(None, pattern=r"^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    is_recurring: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


# ====================== BLOCKED TIMES / HOLIDAYS ======================
class ProviderBlockedTimeResponse(BaseModel):
    id: UUID
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProviderBlockedTimeCreateRequest(BaseModel):
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(extra="forbid")


# ====================== GALLERY ======================
class ProviderGalleryResponse(BaseModel):
    id: UUID
    file_url: str
    file_type: str
    caption: Optional[str] = None
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProviderGalleryCreateRequest(BaseModel):
    file_url: HttpUrl
    file_type: str = Field(..., pattern="^(image|video)$")
    caption: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(extra="forbid")


# ====================== PUBLICATION / MARKETPLACE ======================
class ProviderPublicationRequestResponse(BaseModel):
    id: UUID
    status: str
    requested_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewer_notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ====================== WAITLIST ======================
class ProviderWaitlistResponse(BaseModel):
    id: UUID
    client_id: UUID
    client_name: str
    requested_at: datetime
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ====================== REVIEWS ======================
class ProviderReviewResponse(BaseModel):
    id: UUID
    client_id: UUID
    client_name: str
    rating: float
    comment: Optional[str] = None
    session_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ====================== SUBSCRIPTION ======================
class ProviderSubscriptionResponse(BaseModel):
    id: UUID
    plan_name: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    stripe_subscription_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# ====================== DASHBOARD ======================
class ProviderAppointmentSummary(BaseModel):
    id: UUID
    client_name: str
    appointment_datetime: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)


class ProviderDashboardResponse(BaseModel):
    total_appointments_today: int
    upcoming_sessions: List[ProviderAppointmentSummary]
    total_sessions_this_month: int
    average_rating: float
    profile: ProviderProfileResponse
    publication_status: str
    subscription: Optional[ProviderSubscriptionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    message: str