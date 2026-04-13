# app/modules/organizations/routers/organization_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.dependencies import get_db, get_current_user, get_current_super_admin
from app.modules.organizations.models.organization_model import Organization, OrganizationMember
from app.modules.users.models.user_model import User, UserRole
from app.modules.organizations.schemas.organization_schema import (
    OrganizationCreateRequest,
    OrganizationUpdateRequest,
    OrganizationSettingUpdateRequest,
    OrganizationBrandingUpdateRequest,
    OrganizationBillingInfoUpdateRequest,
    OrganizationInviteCreateRequest,
    OrganizationStatusUpdateRequest,
    OrganizationMemberUpdateRequest,
    OrganizationResponse,
    OrganizationDetailResponse,
    OrganizationListResponse,
    OrganizationSettingResponse,
    OrganizationBrandingResponse,
    OrganizationBillingInfoResponse,
    OrganizationMemberResponse,
    OrganizationMembersListResponse,
    OrganizationInviteResponse,
    OrganizationInvitesListResponse,
    MessageResponse,
)
from app.modules.organizations.services.organization_service import (
    create_organization,
    list_organizations,
    get_organization,
    update_organization,
    update_organization_settings,
    update_organization_branding,
    update_organization_billing_info,
    update_organization_status,
    list_organization_members,
    create_organization_invite,
    list_organization_invites,
    revoke_organization_invite,
    update_organization_member_role,
    remove_organization_member,
    accept_organization_invite,
)

org_router = APIRouter(tags=["Organizations"])


# ====================== EXECUTIVE / SELF ENDPOINTS ======================
@org_router.get("/me", response_model=OrganizationDetailResponse)
def get_my_organization(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the organization the current user belongs to (any active member)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="You are not part of any organization")

    return get_organization(db, member.organization_id, current_user)


@org_router.put("/me", response_model=OrganizationDetailResponse)
def update_my_organization(
    payload: OrganizationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current organization (Owner only)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can update")

    return update_organization(db, member.organization_id, payload, current_user)


@org_router.put("/me/settings", response_model=OrganizationSettingResponse)
def update_my_organization_settings(
    payload: OrganizationSettingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update organization settings (Owner only)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can update settings")

    return update_organization_settings(db, member.organization_id, payload, current_user)


@org_router.put("/me/branding", response_model=OrganizationBrandingResponse)
def update_my_organization_branding(
    payload: OrganizationBrandingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update organization branding (Owner only)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can update branding")

    return update_organization_branding(db, member.organization_id, payload, current_user)


@org_router.put("/me/billing", response_model=OrganizationBillingInfoResponse)
def update_my_organization_billing(
    payload: OrganizationBillingInfoUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update organization billing info (Owner only)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can update billing info")

    return update_organization_billing_info(db, member.organization_id, payload, current_user)


# ====================== MEMBER & INVITE MANAGEMENT (SELF) ======================
@org_router.get("/me/members", response_model=OrganizationMembersListResponse)
def list_my_organization_members(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List all members in current organization (any active member can view)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="You are not part of any organization")

    members, total = list_organization_members(db, member.organization_id, current_user, skip=skip, limit=limit)
    return {
        "total": total,
        "items": members,
        "page": (skip // limit) + 1 if limit else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


@org_router.patch("/me/members/{member_id}", response_model=OrganizationMemberResponse)
def update_my_organization_member_role(
    member_id: UUID,
    payload: OrganizationMemberUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change member role (Owner only)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can manage roles")

    return update_organization_member_role(db, member.organization_id, member_id, payload, current_user)


@org_router.delete("/me/members/{member_id}", response_model=MessageResponse)
def remove_my_organization_member(
    member_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove member from organization (Owner only - cannot remove self or last owner)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can remove members")

    return remove_organization_member(db, member.organization_id, member_id, current_user)


@org_router.post("/me/invites", response_model=OrganizationInviteResponse, status_code=status.HTTP_201_CREATED)
def create_my_organization_invite(
    payload: OrganizationInviteCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Invite new member to organization (Owner only)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can send invites")

    return create_organization_invite(db, member.organization_id, payload, current_user)


@org_router.get("/me/invites", response_model=OrganizationInvitesListResponse)
def list_my_organization_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List pending invites for current organization (Owner only)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can view invites")

    invites, total = list_organization_invites(db, member.organization_id, current_user, skip=skip, limit=limit)
    return {
        "total": total,
        "items": invites,
        "page": (skip // limit) + 1 if limit else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


@org_router.delete("/me/invites/{invite_id}", response_model=MessageResponse)
def revoke_my_organization_invite(
    invite_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Revoke pending invite (Owner only)"""
    member = db.query(OrganizationMember).filter(
        OrganizationMember.user_id == current_user.id,
        OrganizationMember.role_in_org == "owner",
        OrganizationMember.is_active == True
    ).first()

    if not member:
        raise HTTPException(status_code=403, detail="Only organization owner can revoke invites")

    return revoke_organization_invite(db, member.organization_id, invite_id, current_user)


@org_router.post("/invites/{token}/accept", response_model=MessageResponse)
def accept_organization_invite_endpoint(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept organization invite (must be logged in with matching email)"""
    return accept_organization_invite(db, token, current_user)


# ====================== ADMIN / SUPER ADMIN ENDPOINTS ======================
@org_router.post("/", response_model=OrganizationDetailResponse, status_code=status.HTTP_201_CREATED)
def create_organization_endpoint(
    payload: OrganizationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """Super Admin - Create new organization"""
    return create_organization(db, payload, current_user)


@org_router.get("/", response_model=OrganizationListResponse)
def list_organizations_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
    search: Optional[str] = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Super Admin - List all organizations"""
    orgs, total = list_organizations(db, current_user, skip=skip, limit=limit, search=search)

    return {
        "total": total,
        "items": orgs,
        "page": (skip // limit) + 1 if limit else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


@org_router.get("/{org_id}", response_model=OrganizationDetailResponse)
def get_organization_endpoint(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get organization by ID (with proper RBAC)"""
    return get_organization(db, org_id, current_user)


@org_router.put("/{org_id}", response_model=OrganizationDetailResponse)
def update_organization_endpoint(
    org_id: UUID,
    payload: OrganizationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """Super Admin - Update any organization"""
    return update_organization(db, org_id, payload, current_user)


@org_router.patch("/{org_id}/status", response_model=OrganizationDetailResponse)
def update_organization_status_endpoint(
    org_id: UUID,
    payload: OrganizationStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """Super Admin - Update organization status (ACTIVE / SUSPENDED / PENDING)"""
    return update_organization_status(db, org_id, payload, current_user)


@org_router.delete("/{org_id}", response_model=MessageResponse)
def delete_organization_endpoint(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """Super Admin - Soft delete organization"""
    # Service will handle soft delete
    from app.modules.organizations.services.organization_service import soft_delete_organization
    return soft_delete_organization(db, org_id, current_user)