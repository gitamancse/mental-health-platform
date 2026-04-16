from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.modules.admin.services.admin_service import approve_registration, reject_registration, manual_npi_override 
from app.db.session import get_db
from app.core.dependencies import get_current_admin_user
from app.modules.admin.schemas.admin_schema import (
    ProviderRegistrationListItem,
    ProviderOverrideRequest,
    ProviderRegistrationDetailResponse,
    LicenseVerificationInfo,
    ProviderApprovalRequest,
    ProviderRejectionRequest,
    ProviderRevisionRequest,
    StatusUpdateRequest,
    SuspendRequest,
    UnpublishRequest
)
from uuid import UUID
from app.modules.users.models.user_model import User
from typing import Optional
from pydantic import BaseModel, Field


from app.modules.admin.services.admin_service import  AdminService, LicenseVerificationService
router = APIRouter(prefix="/admin/provider")
@router.post("/registrations/{registration_id}/override")
async def override_registration_endpoint(
    registration_id: UUID,
    payload: ProviderOverrideRequest,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint for admins to manually bypass NPI validation failures.
    Must be called BEFORE the approve endpoint if NPI validation failed.
    """
    return manual_npi_override(
        db=db, 
        registration_id=registration_id, 
        admin_id=current_admin.id, 
        reason=payload.reason
    )


@router.post("/registrations/{registration_id}/approve")
async def approve_registration_endpoint(
    registration_id: UUID,
    payload: ProviderApprovalRequest, # <--- Use the specialized schema
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    return approve_registration(
        db, 
        registration_id, 
        current_admin.id, 
        payload.proof_url, 
        payload.admin_notes
    )
@router.post("/registrations/{registration_id}/reject")
async def reject_registration_endpoint(
    registration_id: str,
    rejection_data: dict,
    current_admin: dict = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    return reject_registration(db, registration_id, current_admin["id"], rejection_data["reason"])

# ==================== PENDING LIST ====================
# @router.get(
#     "/pending",
#     response_model=dict,
#     summary="Get List of Pending Provider Registrations",
#     description="Returns a paginated list of providers waiting for admin approval (Vetting Queue)"
# )
# def get_pending_providers(
#     db: Session = Depends(get_db),
#     current_admin = Depends(get_current_admin_user),
#     page: int = Query(1, ge=1, description="Page number"),
#     limit: int = Query(20, ge=1, le=100, description="Number of items per page"),
#     search: Optional[str] = Query(None, description="Search by name or email"),
#     license_state: Optional[str] = Query(None, description="Filter by license state (e.g. CA, TX)"),
#     status: Optional[str] = Query(None, description="Filter by registration status"),
#     state: Optional[str] = None
# ):
#     """Get paginated list of pending provider registrations for Admin Dashboard"""
#     result = AdminService.get_pending_registrations(
#         db=db,
#         page=page,
#         limit=limit,
#         search=search,
#         license_state=license_state,
#         status=status,
#         state_filter=state
#     )
#     return result

@router.get("/pending", response_model=dict)
def get_pending_providers(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or email"),
    license_state: Optional[str] = Query(None, description="Filter by license state (e.g. CA, TX)"),
    status: Optional[str] = Query(None, description="Filter by registration status"),
):
    """Get paginated list of pending provider registrations"""
    result = AdminService.get_pending_registrations(
        db=db,
        page=page,
        limit=limit,
        search=search,
        status_filter=status,           # ← map correctly
        state_filter=license_state      # ← map license_state → state_filter
    )
    return result
 
# ==================== DETAIL VIEW ====================
@router.get(
    "/pending/{registration_id}",
    response_model=ProviderRegistrationDetailResponse,
    summary="Get Provider Registration Detail",            
    description="Returns full details of a specific provider registration for manual review"
)
def get_provider_registration_detail(
    registration_id: UUID,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Get full details of one provider for manual review (includes license verification helper)"""
    detail = AdminService.get_registration_detail(
        db=db,
        registration_id=registration_id
    )
    return detail
 
 
# ==================== LICENSE VERIFICATION HELPER ====================
@router.get(
    "/license-verification",
    response_model=dict,
    summary="Get License Verification URL by State",        
    description="Returns official licensing board name and verification URL for a given US state"
)
async def get_license_verification(
    state: str = Query(
        ...,
        description="US State name or 2-letter code",
        examples="Texas"
    ),
    current_admin = Depends(get_current_admin_user)
):
    """Get license verification details for a state"""
    try:
        result = LicenseVerificationService.get_state_verification(state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
# ==================== ACTION APIs (Write Operations) ====================
 
@router.post("/{registration_id}/approve", summary="Approve Provider Registration")
def approve_provider(
    registration_id: UUID,
    request: ProviderApprovalRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Admin approves a provider after manual verification"""
    return AdminService.approve_registration(
        db=db,
        registration_id=registration_id,
        admin_id=current_admin.id,
        proof_url=request.proof_url,
        admin_notes=request.admin_notes
    )
 
 
@router.post("/{registration_id}/reject", summary="Reject Provider Registration")
def reject_provider(
    registration_id: UUID,
    request: ProviderRejectionRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Admin rejects a provider registration"""
    return AdminService.reject_registration(
        db=db,
        registration_id=registration_id,
        admin_id=current_admin.id,
        reason=request.reason
    )
 
 
@router.post("/{registration_id}/request-revisions", summary="Request Revisions from Provider")
def request_revisions(
    registration_id: UUID,
    request: ProviderRevisionRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Admin asks provider to fix something and resubmit"""
    return AdminService.request_revisions(
        db=db,
        registration_id=registration_id,
        admin_id=current_admin.id,
        feedback=request.feedback
    )
 
# ==================== MANAGEMENT APIs ====================
 
@router.get("", response_model=dict, summary="List All Providers")
def list_all_providers(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status")
):
    """List all providers with filters"""
    return AdminService.list_all_providers(
        db=db, page=page, limit=limit, status=status
    )
 
 
@router.put("/{registration_id}/status", summary="Update Provider Status")
def update_provider_status(
    registration_id: UUID,
    request: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Manually change provider status"""
    return AdminService.update_status(
        db=db,
        registration_id=registration_id,
        new_status=request.status,
        notes=request.notes,
        admin_id=current_admin.id
    )
 
 
@router.post("/{registration_id}/suspend", summary="Suspend Provider")
def suspend_provider(
    registration_id: UUID,
    request: SuspendRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Suspend a provider"""
    return AdminService.suspend_provider(
        db=db,
        registration_id=registration_id,
        admin_id=current_admin.id,
        reason=request.reason
    )
 
 
@router.post("/{registration_id}/unpublish", summary="Unpublish Provider Profile")
def unpublish_provider(
    registration_id: UUID,
    request: UnpublishRequest,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Unpublish provider's public profile"""
    return AdminService.unpublish_provider(
        db=db,
        registration_id=registration_id,
        admin_id=current_admin.id,
        reason=request.reason
    )