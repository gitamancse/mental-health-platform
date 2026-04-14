# app/modules/users/schemas/user_schema.py
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.modules.users.models.user_model import UserRole, AccountStatus
from app.modules.auth.schemas.auth_schema import LicenseCreate
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, ConfigDict



# ====================== PROFILE RESPONSES ======================
class ProviderProfileResponse(BaseModel):
    professional_title: str
    years_of_experience: Optional[int] = None
    bio: Optional[str] = None
    specialties: Optional[List[str]] = None
    modalities: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    insurance_accepted: Optional[List[str]] = None
    office_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    subdomain_slug: Optional[str] = None
    accepting_new_clients: bool = True
    is_published: bool = False
    average_rating: Optional[float] = 0.0
    total_reviews: int = 0
    subscription_tier: Optional[str] = None
    profile_picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ClientProfileResponse(BaseModel):
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    pronouns: Optional[str] = None
    preferred_language: Optional[str] = None
    subscription_tier: Optional[str] = None
    membership_expiry: Optional[datetime] = None
    referral_source: Optional[str] = None
    total_sessions: int = 0
    profile_picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminProfileResponse(BaseModel):
    admin_title: Optional[str] = None
    department: Optional[str] = None
    is_super_admin: bool = False
    permissions: Optional[List[str]] = None
    notes: Optional[str] = None
    profile_picture_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ProviderLicenseResponse(BaseModel):
    id: UUID
    license_number: str
    state: str
    expiry_date: Optional[datetime] = None
    is_verified: bool = False
    verified_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProviderDocumentResponse(BaseModel):
    id: UUID
    file_url: str
    file_type: str
    original_filename: str
    uploaded_at: datetime
    verified: bool = False

    model_config = ConfigDict(from_attributes=True)


# ====================== USER RESPONSES ======================
class UserSummaryResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    account_status: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(BaseModel):
    """Full user profile with all relations"""
    id: UUID
    email: EmailStr
    full_name: str
    phone_number: Optional[str] = None
    profile_picture_url: Optional[str] = None
    role: str
    account_status: str
    is_verified: bool
    is_active: bool
    email_verified: bool
    mfa_enabled: bool = False
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None

    provider_profile: Optional[ProviderProfileResponse] = None
    client_profile: Optional[ClientProfileResponse] = None
    admin_profile: Optional[AdminProfileResponse] = None

    licenses: List[ProviderLicenseResponse] = Field(default_factory=list)
    documents: List[ProviderDocumentResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# ====================== REQUEST SCHEMAS ======================
class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, pattern=r"^\+?\d{10,15}$")
    profile_picture_url: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class ProviderProfileUpdateRequest(BaseModel):
    professional_title: Optional[str] = Field(None, max_length=100)
    years_of_experience: Optional[int] = Field(None, ge=0)
    bio: Optional[str] = Field(None, max_length=2000)
    specialties: Optional[List[str]] = None
    modalities: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    insurance_accepted: Optional[List[str]] = None
    office_address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = Field(None, max_length=50)
    accepting_new_clients: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")


class ClientProfileUpdateRequest(BaseModel):
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = Field(None, max_length=50)
    pronouns: Optional[str] = Field(None, max_length=50)
    preferred_language: Optional[str] = Field(None, max_length=50)
    preferences: Optional[dict] = None

    model_config = ConfigDict(extra="forbid")


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=12, max_length=128)
    confirm_new_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_new_password:
            raise ValueError("New passwords do not match")
        return self

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str):
        if (not any(c.isupper() for c in v) or
            not any(c.isdigit() for c in v) or
            not any(c in "!@#$%^&*()_+-=" for c in v)):
            raise ValueError("Password must contain uppercase, number and special character")
        return v


class UserStatusUpdateRequest(BaseModel):
    account_status: AccountStatus
    notes: Optional[str] = Field(None, max_length=1000)


class ProviderPublishRequest(BaseModel):
    is_published: bool
    reason: Optional[str] = None


class UserListResponse(BaseModel):
    total: int
    items: List[UserSummaryResponse]
    page: int
    size: int
    pages: int


class MessageResponse(BaseModel):
    message: str