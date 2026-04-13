# app/modules/executive/schemas/executive_schema.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, EmailStr

from app.modules.organizations.models.organization_model import OrgStatus


# ====================== DASHBOARD ======================
class ExecutiveOrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: OrgStatus
    logo_url: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutiveProviderSummaryResponse(BaseModel):
    id: UUID
    full_name: str
    professional_title: str
    is_published: bool
    account_status: str
    average_rating: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ExecutiveDashboardResponse(BaseModel):
    total_providers: int
    total_clients: int
    active_sessions_today: int
    pending_approvals: int
    total_revenue_this_month: float = 0.0
    organization: ExecutiveOrganizationResponse
    recent_providers: List[ExecutiveProviderSummaryResponse]

    model_config = ConfigDict(from_attributes=True)


# ====================== CLINIC STAFF ======================
class ClinicStaffResponse(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: EmailStr
    role: str
    is_active: bool
    hired_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClinicStaffCreateRequest(BaseModel):
    email: EmailStr
    role: str = Field(..., pattern="^(receptionist|billing_specialist|manager|coordinator|admin_assistant)$")
    full_name: str = Field(..., min_length=3, max_length=255)

    model_config = ConfigDict(extra="forbid")


class ClinicStaffUpdateRequest(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


# ====================== ANNOUNCEMENTS ======================
class ClinicAnnouncementResponse(BaseModel):
    id: UUID
    title: str
    content: str
    priority: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    created_by_name: str

    model_config = ConfigDict(from_attributes=True)


class ClinicAnnouncementCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    content: str = Field(..., max_length=2000)
    priority: str = Field("normal", pattern="^(normal|high|urgent)$")
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")


class ClinicAnnouncementUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=2000)
    priority: Optional[str] = Field(None, pattern="^(normal|high|urgent)$")
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(extra="forbid")


# ====================== PERMISSIONS & ACTIVITY LOGS ======================
class ExecutivePermissionResponse(BaseModel):
    id: UUID
    permission: str
    granted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExecutiveActivityLogResponse(BaseModel):
    id: UUID
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ====================== COMMON ======================
class MessageResponse(BaseModel):
    message: str