from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.modules.provider.services.admin_service import approve_registration, reject_registration, manual_npi_override 
from app.db.session import get_db
from app.core.dependencies import get_current_admin_user
from app.modules.provider.schemas.admin_schema import ProviderApprovalRequest, ProviderRejectionRequest
from uuid import UUID
from app.modules.users.models.user_model import User

from app.modules.provider.schemas.admin_schema import ProviderOverrideRequest # Import new schema
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