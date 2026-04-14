# app/modules/provider/schemas/admin_schema.py
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