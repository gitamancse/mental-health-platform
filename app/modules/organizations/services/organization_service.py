# app/modules/organizations/services/organization_service.py
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session, joinedload

from app.modules.organizations.models.organization_model import (
    Organization, OrganizationMember, OrganizationSetting,
    OrganizationBillingInfo, OrganizationBranding, OrganizationInvite,
    OrgStatus
)
from app.modules.users.models.user_model import User, UserRole
from app.modules.organizations.schemas.organization_schema import (
    OrganizationCreateRequest, OrganizationUpdateRequest,
    OrganizationSettingUpdateRequest, OrganizationBrandingUpdateRequest,
    OrganizationBillingInfoUpdateRequest,
    OrganizationInviteCreateRequest, OrganizationMemberUpdateRequest,
    OrganizationStatusUpdateRequest,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ====================== PRIVATE HELPERS ======================
def _get_organization_with_relations(db: Session, org_id: UUID) -> Organization:
    org = (
        db.query(Organization)
        .options(
            joinedload(Organization.members),
            joinedload(Organization.settings),
            joinedload(Organization.billing_info),
        )
        .filter(Organization.id == org_id, Organization.deleted_at.is_(None))
        .first()
    )
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org


def _ensure_owner(db: Session, org_id: UUID, current_user: User) -> None:
    """Helper to enforce owner-level permission"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()
    if not member and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Organization owner access required")


# ====================== PUBLIC SERVICE FUNCTIONS ======================
def create_organization(
    db: Session, payload: OrganizationCreateRequest, created_by: User
) -> Organization:
    """Super Admin only - Create new organization"""
    if created_by.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")

    if db.query(Organization).filter(Organization.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Organization email already exists")

    # Generate unique slug
    base_slug = payload.name.lower().replace(" ", "-").replace(".", "")
    slug = base_slug
    counter = 1
    while db.query(Organization).filter(Organization.slug == slug).first():
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(
        name=payload.name,
        slug=slug,
        legal_name=payload.legal_name,
        email=payload.email,
        phone_number=payload.phone_number,
        website=str(payload.website) if payload.website else None,
        address_line1=payload.address_line1,
        city=payload.city,
        state=payload.state,
        country=payload.country,
        postal_code=payload.postal_code,
        status=OrgStatus.ACTIVE,
        # org_type column assumed added to model
    )
    db.add(org)
    db.flush()

    # Create default related records
    db.add(OrganizationSetting(organization_id=org.id))
    db.add(OrganizationBillingInfo(organization_id=org.id))
    db.add(OrganizationBranding(organization_id=org.id))

    # Add creator as owner
    db.add(OrganizationMember(
        organization_id=org.id,
        user_id=created_by.id,
        role_in_org="owner",
        is_active=True
    ))

    db.commit()
    db.refresh(org)
    return org


def list_organizations(
    db: Session,
    current_user: User,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
) -> Tuple[List[Organization], int]:
    """Super Admin only"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")

    query = db.query(Organization).filter(Organization.deleted_at.is_(None))

    if search:
        query = query.filter(
            or_(
                Organization.name.ilike(f"%{search}%"),
                Organization.email.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    orgs = query.order_by(Organization.created_at.desc()).offset(skip).limit(limit).all()
    return orgs, total


def get_organization(db: Session, org_id: UUID, current_user: User) -> Organization:
    """Executive can only see their own organization"""
    org = _get_organization_with_relations(db, org_id)

    if current_user.role == UserRole.SUPER_ADMIN:
        return org

    member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="You do not have access to this organization")

    return org


def update_organization(
    db: Session, org_id: UUID, payload: OrganizationUpdateRequest, current_user: User
) -> Organization:
    """Super Admin or Organization Owner can update"""
    org = _get_organization_with_relations(db, org_id)

    if current_user.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN):
        _ensure_owner(db, org_id, current_user)

    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(org, field):
            setattr(org, field, value)

    # If name changed, optionally regenerate slug (business decision - here we keep existing)
    org.updated_at = utc_now()
    db.commit()
    db.refresh(org)
    return org


def update_organization_settings(
    db: Session, org_id: UUID, payload: OrganizationSettingUpdateRequest, current_user: User
) -> OrganizationSetting:
    """Owner only"""
    org = _get_organization_with_relations(db, org_id)
    _ensure_owner(db, org_id, current_user)

    settings = org.settings
    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(settings, field):
            setattr(settings, field, value)

    settings.updated_at = utc_now()
    db.commit()
    db.refresh(settings)
    return settings


def update_organization_branding(
    db: Session, org_id: UUID, payload: OrganizationBrandingUpdateRequest, current_user: User
) -> OrganizationBranding:
    """Owner only"""
    org = _get_organization_with_relations(db, org_id)
    _ensure_owner(db, org_id, current_user)

    branding = org.branding
    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(branding, field):
            setattr(branding, field, value)

    db.commit()
    db.refresh(branding)
    return branding


def update_organization_billing_info(
    db: Session, org_id: UUID, payload: OrganizationBillingInfoUpdateRequest, current_user: User
) -> OrganizationBillingInfo:
    """Owner only"""
    org = _get_organization_with_relations(db, org_id)
    _ensure_owner(db, org_id, current_user)

    billing = org.billing_info
    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(billing, field):
            setattr(billing, field, value)

    billing.updated_at = utc_now()
    db.commit()
    db.refresh(billing)
    return billing


def update_organization_status(
    db: Session, org_id: UUID, payload: OrganizationStatusUpdateRequest, current_user: User
) -> Organization:
    """Super Admin only"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")

    org = _get_organization_with_relations(db, org_id)
    org.status = payload.status
    org.updated_at = utc_now()
    db.commit()
    db.refresh(org)
    return org


def soft_delete_organization(db: Session, org_id: UUID, current_user: User) -> dict:
    """Super Admin only - soft delete"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")

    org = _get_organization_with_relations(db, org_id)
    org.deleted_at = utc_now()
    db.commit()
    return {"message": "Organization soft-deleted successfully"}


# ====================== MEMBER MANAGEMENT ======================
def list_organization_members(
    db: Session, org_id: UUID, current_user: User, skip: int = 0, limit: int = 20
) -> Tuple[List[dict], int]:
    """Any active member can list members (joined with User for full_name/email)"""
    # Permission: any member
    member_exists = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == org_id,
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True
    ).first()
    if not member_exists and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="No access to this organization")

    query = (
        db.query(OrganizationMember)
        .join(User, OrganizationMember.user_id == User.id)
        .filter(OrganizationMember.organization_id == org_id)
        .options(joinedload(OrganizationMember.user))
    )

    total = query.count()
    members = query.order_by(OrganizationMember.joined_at.desc()).offset(skip).limit(limit).all()

    # Convert to dict for Pydantic (full_name and email come from joined User)
    result = []
    for m in members:
        result.append({
            "id": m.id,
            "user_id": m.user_id,
            "full_name": m.user.full_name,
            "email": m.user.email,
            "role_in_org": m.role_in_org,
            "is_active": m.is_active,
            "joined_at": m.joined_at,
        })
    return result, total


def update_organization_member_role(
    db: Session, org_id: UUID, member_id: UUID, payload: OrganizationMemberUpdateRequest, current_user: User
) -> dict:
    """Owner only"""
    _ensure_owner(db, org_id, current_user)

    member = db.query(OrganizationMember).filter(
        OrganizationMember.id == member_id,
        OrganizationMember.organization_id == org_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Prevent removing the last owner
    if payload.role_in_org != "owner":
        owner_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.role_in_org == "owner",
            OrganizationMember.is_active == True
        ).count()
        if owner_count == 1 and member.role_in_org == "owner":
            raise HTTPException(status_code=400, detail="Cannot change the last owner's role")

    member.role_in_org = payload.role_in_org
    db.commit()
    db.refresh(member)

    return {
        "id": member.id,
        "user_id": member.user_id,
        "full_name": member.user.full_name,
        "email": member.user.email,
        "role_in_org": member.role_in_org,
        "is_active": member.is_active,
        "joined_at": member.joined_at,
    }


def remove_organization_member(
    db: Session, org_id: UUID, member_id: UUID, current_user: User
) -> dict:
    """Owner only - cannot remove self or last owner"""
    _ensure_owner(db, org_id, current_user)

    member = db.query(OrganizationMember).filter(
        OrganizationMember.id == member_id,
        OrganizationMember.organization_id == org_id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")

    # Prevent removing the last owner
    if member.role_in_org == "owner":
        owner_count = db.query(OrganizationMember).filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.role_in_org == "owner",
            OrganizationMember.is_active == True
        ).count()
        if owner_count == 1:
            raise HTTPException(status_code=400, detail="Cannot remove the last owner")

    member.is_active = False
    db.commit()
    return {"message": "Member removed successfully"}


# ====================== INVITE MANAGEMENT ======================
def create_organization_invite(
    db: Session, org_id: UUID, payload: OrganizationInviteCreateRequest, invited_by: User
) -> OrganizationInvite:
    """Owner only"""
    _ensure_owner(db, org_id, invited_by)

    # Check if already a member
    existing_member = db.query(OrganizationMember).join(User).filter(
        OrganizationMember.organization_id == org_id,
        User.email == payload.email
    ).first()
    if existing_member:
        raise HTTPException(status_code=409, detail="User is already a member")

    # Check pending invite
    existing_invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.organization_id == org_id,
        OrganizationInvite.email == payload.email,
        OrganizationInvite.accepted_at.is_(None),
        OrganizationInvite.expires_at > utc_now()
    ).first()
    if existing_invite:
        raise HTTPException(status_code=409, detail="Pending invite already exists for this email")

    invite = OrganizationInvite(
        organization_id=org_id,
        email=payload.email,
        invited_by=invited_by.id,
        role_in_org=payload.role_in_org,
        token=str(uuid4()),
        expires_at=utc_now() + timedelta(days=7),
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def list_organization_invites(
    db: Session, org_id: UUID, current_user: User, skip: int = 0, limit: int = 20
) -> Tuple[List[OrganizationInvite], int]:
    """Owner only"""
    _ensure_owner(db, org_id, current_user)

    query = db.query(OrganizationInvite).filter(
        OrganizationInvite.organization_id == org_id,
        OrganizationInvite.accepted_at.is_(None),
        OrganizationInvite.expires_at > utc_now()
    )

    total = query.count()
    invites = query.order_by(OrganizationInvite.created_at.desc()).offset(skip).limit(limit).all()
    return invites, total


def revoke_organization_invite(
    db: Session, org_id: UUID, invite_id: UUID, current_user: User
) -> dict:
    """Owner only"""
    _ensure_owner(db, org_id, current_user)

    invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.id == invite_id,
        OrganizationInvite.organization_id == org_id
    ).first()
    if not invite or invite.accepted_at:
        raise HTTPException(status_code=404, detail="Active invite not found")

    db.delete(invite)
    db.commit()
    return {"message": "Invite revoked successfully"}


def accept_organization_invite(db: Session, token: str, current_user: User) -> dict:
    """Public invite acceptance - user must be logged in with matching email"""
    invite = db.query(OrganizationInvite).filter(
        OrganizationInvite.token == token,
        OrganizationInvite.accepted_at.is_(None),
        OrganizationInvite.expires_at > utc_now()
    ).first()

    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or expired")

    if invite.email != current_user.email:
        raise HTTPException(status_code=403, detail="Invite email does not match your account")

    # Check if already a member
    existing = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == invite.organization_id,
        OrganizationMember.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="You are already a member")

    # Add as member
    db.add(OrganizationMember(
        organization_id=invite.organization_id,
        user_id=current_user.id,
        role_in_org=invite.role_in_org,
        is_active=True
    ))

    invite.accepted_at = utc_now()
    db.commit()
    return {"message": "Invite accepted successfully. You are now a member of the organization."}