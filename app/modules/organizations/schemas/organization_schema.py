# app/modules/organizations/schemas/organization_schema.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, EmailStr, HttpUrl

from app.modules.organizations.models.organization_model import OrgStatus, OrgType


# ====================== BASE RESPONSES ======================
class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    legal_name: Optional[str] = None
    email: EmailStr
    phone_number: Optional[str] = None
    status: OrgStatus
    logo_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationDetailResponse(OrganizationResponse):
    """Full organization with nested data"""
    tax_id: Optional[str] = None
    website: Optional[HttpUrl] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    settings: Optional["OrganizationSettingResponse"] = None
    billing_info: Optional["OrganizationBillingInfoResponse"] = None
    branding: Optional["OrganizationBrandingResponse"] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationListResponse(BaseModel):
    total: int
    items: List[OrganizationResponse]
    page: int
    size: int
    pages: int


# ====================== SETTINGS & BRANDING ======================
class OrganizationSettingResponse(BaseModel):
    timezone: str
    default_session_duration: int
    allow_self_booking: bool
    require_approval_for_new_clients: bool
    custom_config: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationSettingUpdateRequest(BaseModel):
    timezone: Optional[str] = None
    default_session_duration: Optional[int] = Field(None, ge=15, le=180)
    allow_self_booking: Optional[bool] = None
    require_approval_for_new_clients: Optional[bool] = None
    custom_config: Optional[dict] = None

    model_config = ConfigDict(extra="forbid")


class OrganizationBrandingResponse(BaseModel):
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    custom_domain: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationBrandingUpdateRequest(BaseModel):
    primary_color: Optional[str] = Field(None, pattern=r"^#([A-Fa-f0-9]{6})$")
    secondary_color: Optional[str] = Field(None, pattern=r"^#([A-Fa-f0-9]{6})$")
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    custom_domain: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class OrganizationBillingInfoResponse(BaseModel):
    stripe_customer_id: Optional[str] = None
    stripe_connect_account_id: Optional[str] = None
    billing_email: Optional[EmailStr] = None
    billing_address: Optional[str] = None
    tax_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationBillingInfoUpdateRequest(BaseModel):
    billing_email: Optional[EmailStr] = None
    billing_address: Optional[str] = None
    tax_id: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


# ====================== MEMBERS & INVITES ======================
class OrganizationMemberResponse(BaseModel):
    id: UUID
    user_id: UUID
    full_name: str
    email: EmailStr
    role_in_org: str
    is_active: bool
    joined_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrganizationMembersListResponse(BaseModel):
    total: int
    items: List[OrganizationMemberResponse]
    page: int
    size: int
    pages: int


class OrganizationMemberUpdateRequest(BaseModel):
    role_in_org: str = Field(..., pattern=r"^(owner|manager|staff)$")

    model_config = ConfigDict(extra="forbid")


class OrganizationInviteCreateRequest(BaseModel):
    email: EmailStr
    role_in_org: str = Field(..., pattern=r"^(owner|manager|staff)$")

    model_config = ConfigDict(extra="forbid")


class OrganizationInviteResponse(BaseModel):
    id: UUID
    email: EmailStr
    role_in_org: str
    expires_at: datetime
    accepted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OrganizationInvitesListResponse(BaseModel):
    total: int
    items: List[OrganizationInviteResponse]
    page: int
    size: int
    pages: int


# ====================== ADMIN / STATUS ======================
class OrganizationStatusUpdateRequest(BaseModel):
    status: OrgStatus

    model_config = ConfigDict(extra="forbid")


# ====================== REQUEST SCHEMAS ======================
class OrganizationCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    email: EmailStr
    phone_number: Optional[str] = Field(None, pattern=r"^\+?\d{10,15}$")
    website: Optional[HttpUrl] = None
    org_type: OrgType = OrgType.CLINIC

    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "IN"
    postal_code: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class OrganizationUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, pattern=r"^\+?\d{10,15}$")
    website: Optional[HttpUrl] = None

    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class MessageResponse(BaseModel):
    message: str