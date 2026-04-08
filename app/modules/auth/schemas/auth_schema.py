# app/modules/auth/schemas/auth_schema.py
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterClientRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    confirm_password: str
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, pattern=r"^\+?\d{10,15}$")

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str):
        if not any(c.isupper() for c in v) or not any(c.isdigit() for c in v) or not any(c in "!@#$%^&*()_+-=" for c in v):
            raise ValueError("Password must contain uppercase, number and special character")
        return v


class LicenseCreate(BaseModel):
    license_number: str = Field(..., min_length=5)
    state: str = Field(..., min_length=2, max_length=2)
    expiry_date: Optional[datetime] = None


class RegisterProviderRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    confirm_password: str
    full_name: str = Field(..., min_length=2, max_length=255)
    phone_number: Optional[str] = None

    professional_title: str
    years_of_experience: Optional[int] = None
    bio: Optional[str] = None
    specialties: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)

    licenses: List[LicenseCreate] = Field(..., min_length=1)   # At least one license required

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class RegisterAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12, max_length=128)
    confirm_password: str
    full_name: str
    admin_title: Optional[str] = None
    department: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


# Existing schemas (Token, UserMeResponse, etc.) remain unchanged...
class UserMeResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_verified: bool
    account_status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class VerifyEmailResponse(BaseModel):
    message: str