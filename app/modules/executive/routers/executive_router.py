# app/modules/executive/routers/executive_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from pydantic import EmailStr

from app.core.dependencies import get_db, get_current_user
from app.modules.users.models.user_model import User, UserRole
from app.modules.organizations.models.organization_model import OrganizationMember
from app.modules.executive.schemas.executive_schema import (
    ExecutiveDashboardResponse,
    ClinicStaffResponse,
    ClinicStaffCreateRequest,
    ClinicStaffUpdateRequest,
    ClinicAnnouncementResponse,
    ClinicAnnouncementCreateRequest,
    ClinicAnnouncementUpdateRequest,
    ExecutivePermissionResponse,
    ExecutiveActivityLogResponse,
    MessageResponse,
)
from app.modules.executive.services.executive_service import (
    get_executive_dashboard,
    list_clinic_staff,
    create_clinic_staff,
    update_clinic_staff,
    remove_clinic_staff,
    list_announcements,
    create_announcement,
    update_announcement,
    delete_announcement,
    list_my_permissions,
    list_activity_logs,
    invite_clinic_member,
)

executive_router = APIRouter(prefix="/executives", tags=["Executives"])


# ====================== DASHBOARD ======================
@executive_router.get("/me/dashboard", response_model=ExecutiveDashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Executive / Clinic Owner Dashboard"""
    
    # Same membership check as /organizations/me (this was the missing piece)
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active organization found for this executive"
        )

    # Now safely call the service (it can assume the user has an org)
    return get_executive_dashboard(db, current_user)


# ====================== CLINIC STAFF MANAGEMENT ======================
@executive_router.get("/me/staff", response_model=List[ClinicStaffResponse])
def list_my_staff(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List all clinic staff (receptionists, billing, etc.)"""
    return list_clinic_staff(db, current_user, skip, limit)


@executive_router.post("/me/staff", response_model=ClinicStaffResponse, status_code=status.HTTP_201_CREATED)
def add_clinic_staff(
    payload: ClinicStaffCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add new clinic staff member"""
    return create_clinic_staff(db, current_user, payload)


@executive_router.put("/me/staff/{staff_id}", response_model=ClinicStaffResponse)
def update_clinic_staff_endpoint(
    staff_id: UUID,
    payload: ClinicStaffUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update staff role or status"""
    return update_clinic_staff(db, current_user, staff_id, payload)


@executive_router.delete("/me/staff/{staff_id}", response_model=MessageResponse)
def remove_clinic_staff_endpoint(
    staff_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove / deactivate staff member"""
    return remove_clinic_staff(db, current_user, staff_id)


# ====================== CLINIC ANNOUNCEMENTS ======================
@executive_router.get("/me/announcements", response_model=List[ClinicAnnouncementResponse])
def list_my_announcements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all active clinic announcements"""
    return list_announcements(db, current_user)


@executive_router.post("/me/announcements", response_model=ClinicAnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement_endpoint(
    payload: ClinicAnnouncementCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create new clinic-wide announcement"""
    return create_announcement(db, current_user, payload)


@executive_router.put("/me/announcements/{announcement_id}", response_model=ClinicAnnouncementResponse)
def update_announcement_endpoint(
    announcement_id: UUID,
    payload: ClinicAnnouncementUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update announcement"""
    return update_announcement(db, current_user, announcement_id, payload)


@executive_router.delete("/me/announcements/{announcement_id}", response_model=MessageResponse)
def delete_announcement_endpoint(
    announcement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete announcement"""
    return delete_announcement(db, current_user, announcement_id)


# ====================== PERMISSIONS & ACTIVITY ======================
@executive_router.get("/me/permissions", response_model=List[ExecutivePermissionResponse])
def get_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View my own executive permissions"""
    return list_my_permissions(db, current_user)


@executive_router.get("/me/activity-logs", response_model=List[ExecutiveActivityLogResponse])
def get_activity_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """View executive activity audit log"""
    return list_activity_logs(db, current_user, skip, limit)


# ====================== INVITES ======================
@executive_router.post("/me/invite-staff", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def invite_clinic_staff_endpoint(
    email: EmailStr,
    role: str = Query(..., pattern="^(receptionist|billing_specialist|manager|coordinator|admin_assistant)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invite new staff member to the clinic/organization"""
    return invite_clinic_member(db, current_user, email, role)