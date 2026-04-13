# app/modules/executive/services/executive_service.py
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.modules.users.models.user_model import User, UserRole
from app.modules.organizations.models.organization_model import (
    Organization, OrganizationMember, OrganizationInvite
)
from app.modules.executive.models.executive_model import (
    ClinicStaff, ClinicAnnouncement, ExecutivePermission, ExecutiveActivityLog
)
from app.modules.users.models.user_model import ProviderProfile
from app.modules.executive.schemas.executive_schema import (
    ClinicStaffCreateRequest,
    ClinicStaffUpdateRequest,
    ClinicAnnouncementCreateRequest,
    ClinicAnnouncementUpdateRequest,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ====================== PRIVATE HELPERS ======================
def _ensure_executive(db: Session, current_user: User) -> Organization:
    """Ensure user is an Executive and return their Organization"""
    if current_user.role != UserRole.EXECUTIVE:
        raise HTTPException(status_code=403, detail="Executive access required")

    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True,
        OrganizationMember.role_in_org.in_(["owner", "manager", "executive"])
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="No active organization found for this executive")

    org = db.query(Organization).filter(Organization.id == member.organization_id).first()
    if not org or org.deleted_at:
        raise HTTPException(status_code=404, detail="Organization not found")

    return org


# ====================== DASHBOARD ======================
def get_executive_dashboard(db: Session, current_user: User):
    org = _ensure_executive(db, current_user)

    total_providers = db.query(ProviderProfile).filter(
        ProviderProfile.user.has(organization_id=org.id)
    ).count()

    # TODO: Replace with real session & billing queries when those modules are ready
    total_clients = 0
    active_sessions_today = 0
    total_revenue_this_month = 0.0
    pending_approvals = db.query(ProviderProfile).filter(
        ProviderProfile.user.has(organization_id=org.id),
        ProviderProfile.is_published == False
    ).count()

    recent_providers = db.query(ProviderProfile).join(User).filter(
        ProviderProfile.user.has(organization_id=org.id)
    ).order_by(ProviderProfile.created_at.desc()).limit(5).all()

    return {
        "total_providers": total_providers,
        "total_clients": total_clients,
        "active_sessions_today": active_sessions_today,
        "pending_approvals": pending_approvals,
        "total_revenue_this_month": total_revenue_this_month,
        "organization": org,
        "recent_providers": recent_providers,
    }


# ====================== CLINIC STAFF ======================
def list_clinic_staff(db: Session, current_user: User, skip: int = 0, limit: int = 50):
    org = _ensure_executive(db, current_user)

    query = db.query(ClinicStaff).join(User).filter(
        ClinicStaff.organization_id == org.id
    ).options(joinedload(ClinicStaff.user))

    items = query.order_by(ClinicStaff.hired_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "full_name": s.user.full_name,
            "email": s.user.email,
            "role": s.role,
            "is_active": s.is_active,
            "hired_at": s.hired_at,
        }
        for s in items
    ]


def create_clinic_staff(db: Session, current_user: User, payload: ClinicStaffCreateRequest):
    org = _ensure_executive(db, current_user)

    # In real implementation you would send an invite and create after acceptance.
    # For simplicity we create directly (you can change to invite flow later)
    staff = ClinicStaff(
        organization_id=org.id,
        user_id=None,  # placeholder until user is created via invite
        role=payload.role,
        hired_at=utc_now(),
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff  # In real code you would return full user info after invite acceptance


def update_clinic_staff(db: Session, current_user: User, staff_id: UUID, payload: ClinicStaffUpdateRequest):
    org = _ensure_executive(db, current_user)

    staff = db.query(ClinicStaff).filter(
        ClinicStaff.id == staff_id,
        ClinicStaff.organization_id == org.id
    ).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(staff, field, value)

    db.commit()
    db.refresh(staff)
    return staff


def remove_clinic_staff(db: Session, current_user: User, staff_id: UUID):
    org = _ensure_executive(db, current_user)

    staff = db.query(ClinicStaff).filter(
        ClinicStaff.id == staff_id,
        ClinicStaff.organization_id == org.id
    ).first()
    if not staff:
        raise HTTPException(status_code=404, detail="Staff member not found")

    staff.is_active = False
    db.commit()
    return {"message": "Staff member deactivated successfully"}


# ====================== ANNOUNCEMENTS ======================
def list_announcements(db: Session, current_user: User):
    org = _ensure_executive(db, current_user)

    return db.query(ClinicAnnouncement).filter(
        ClinicAnnouncement.organization_id == org.id,
        (ClinicAnnouncement.expires_at.is_(None)) | (ClinicAnnouncement.expires_at > utc_now())
    ).order_by(ClinicAnnouncement.created_at.desc()).all()


def create_announcement(db: Session, current_user: User, payload: ClinicAnnouncementCreateRequest):
    org = _ensure_executive(db, current_user)

    announcement = ClinicAnnouncement(
        organization_id=org.id,
        created_by=current_user.id,
        **payload.model_dump()
    )
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    return announcement


def update_announcement(db: Session, current_user: User, announcement_id: UUID, payload: ClinicAnnouncementUpdateRequest):
    org = _ensure_executive(db, current_user)

    announcement = db.query(ClinicAnnouncement).filter(
        ClinicAnnouncement.id == announcement_id,
        ClinicAnnouncement.organization_id == org.id
    ).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(announcement, field, value)

    db.commit()
    db.refresh(announcement)
    return announcement


def delete_announcement(db: Session, current_user: User, announcement_id: UUID):
    org = _ensure_executive(db, current_user)

    announcement = db.query(ClinicAnnouncement).filter(
        ClinicAnnouncement.id == announcement_id,
        ClinicAnnouncement.organization_id == org.id
    ).first()
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")

    db.delete(announcement)
    db.commit()
    return {"message": "Announcement deleted successfully"}


# ====================== PERMISSIONS & LOGS ======================
def list_my_permissions(db: Session, current_user: User):
    # Executive permissions are stored in ExecutivePermission table
    return db.query(ExecutivePermission).filter(
        ExecutivePermission.executive_id == current_user.executive_profile.id  # assumes executive_profile exists
    ).all()


def list_activity_logs(db: Session, current_user: User, skip: int = 0, limit: int = 50):
    return db.query(ExecutiveActivityLog).filter(
        ExecutiveActivityLog.executive_id == current_user.executive_profile.id
    ).order_by(ExecutiveActivityLog.created_at.desc()).offset(skip).limit(limit).all()


# ====================== INVITE ======================
def invite_clinic_member(db: Session, current_user: User, email: str, role: str):
    org = _ensure_executive(db, current_user)

    # Reuse the same OrganizationInvite system
    invite = OrganizationInvite(
        organization_id=org.id,
        email=email,
        invited_by=current_user.id,
        role_in_org="staff",           # or map to specific role
        token=str(UUID(int=0)),        # replace with secure token generator in production
        expires_at=utc_now() + timezone.timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    # TODO: Send email with invite link (use background task + email service)
    return {"message": f"Invitation sent to {email} for role: {role}"}