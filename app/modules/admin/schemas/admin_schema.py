# app/modules/provider/schemas/admin_provider.py

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# --- Generic Audit Log Schemas ---

class AdminActionBase(BaseModel):
    action_type: str
    target_id: UUID
    target_type: str
    action_metadata: Optional[Dict[str, Any]] = None

class AdminActionResponse(AdminActionBase):
    id: UUID
    admin_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# --- Specialized Provider Review Schemas ---

class ProviderApprovalRequest(BaseModel):
    """Schema for the Approve endpoint"""
    proof_url: str = Field(
        ..., 
        description="URL to the screenshot/document proving state board license verification"
    )
    admin_notes: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Internal notes regarding the verification process"
    )

class ProviderRejectionRequest(BaseModel):
    """Schema for the Reject endpoint"""
    reason: str = Field(
        ..., 
        min_length=10, 
        max_length=1000, 
        description="Reason for rejection, which will be shown to the provider"
    )

class ProviderRevisionRequest(BaseModel):
    """Schema for requesting revisions (e.g., 'Please re-upload license')"""
    feedback: str = Field(..., min_length=5)
class ProviderOverrideRequest(BaseModel):
    reason: str = Field(
        ..., 
        min_length=10, 
        max_length=500, 
        description="Detailed explanation of why the automated NPI check is being bypassed"
    )
 
 
# ==================== LICENSE VERFICIATION ====================
 
class LicenseVerificationInfo(BaseModel):
    state: str
    licensing_board: Optional[str] = None
    verification_url: Optional[str] = None
    message: str
    success: bool
 
# ==================== LIST OF PENDING PROVIDER ====================
 
class ProviderRegistrationListItem(BaseModel):
    """Simplified to match the new registration payload"""
    id: UUID
    first_name: str
    last_name: str
    email: str
    npi_number: str
    npi_type: str
    status: str
    submitted_at: datetime
    npi_validated: bool
    admin_override: bool
    state: str
    city: str

    class Config:
        from_attributes = True
# ==================== PARTICULAR PROVIDER DETAILS ====================
 
class ProviderRegistrationDetailResponse(BaseModel):
    """Full details of what the provider submitted during registration"""
    id: UUID
    user_id: UUID
    title: str
    first_name: str
    last_name: str
    email: str
    phone_number: Optional[str] = None
    
    # Address
    address: str
    city: str
    state: str
    zip_code: str
    
    # Professional
    academic_degree: str
    npi_type: str
    npi_number: str
    npi_validated: bool
    
    # Status & Audit
    status: str
    admin_override: bool
    override_reason: Optional[str] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    submitted_at: datetime

    class Config:
        from_attributes = True
 
# ==================== ACTION REQUEST SCHEMAS ====================
 
class ProviderApprovalRequest(BaseModel):
    """Request body for approving a provider"""
    proof_url: str = Field(..., description="URL of the proof/screenshot that license was manually verified")
    admin_notes: Optional[str] = Field(None, max_length=1000, description="Internal notes by admin")
 
 
class ProviderRejectionRequest(BaseModel):
    """Request body for rejecting a provider"""
    reason: str = Field(..., min_length=10, max_length=1000, description="Reason for rejection (will be sent to provider)")
 
 
class ProviderRevisionRequest(BaseModel):
    """Request body for asking provider to make changes"""
    feedback: str = Field(..., min_length=10, max_length=1000, description="Feedback on what needs to be fixed")
 
 
# ==================== ACTION STATUS ====================
 
class StatusUpdateRequest(BaseModel):
    """For PUT /status"""
    status: str = Field(..., description="New status value")
    notes: Optional[str] = Field(None, max_length=1000)
 
# ==================== SUSPENDION REQUEST ====================
 
class SuspendRequest(BaseModel):
    reason: str = Field(..., min_length=10, max_length=1000, description="Reason for suspension")
 
# ==================== UNPUBLISH PROVIDER ====================
 
class UnpublishRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=1000, description="Reason for unpublishing")
