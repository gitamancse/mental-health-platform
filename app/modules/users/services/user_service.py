# app/modules/users/services/user_service.py
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.modules.auth.services.auth_service import get_password_hash, verify_password
from app.modules.users.models.user_model import (
    User, UserRole, AccountStatus, AuditLog, AdminActivityLog
)
   # Correct import

from app.modules.users.schemas.user_schema import (
    UserUpdateRequest, ProviderProfileUpdateRequest,
    ClientProfileUpdateRequest, ChangePasswordRequest,
    UserStatusUpdateRequest, ProviderPublishRequest, LicenseCreate
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ====================== AUDIT HELPERS ======================
def log_audit(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: Optional[UUID],
    details: Optional[dict] = None,
    performed_by: UUID = None,
    target_user_id: Optional[UUID] = None,
    ip_address: Optional[str] = None,
) -> None:
    audit = AuditLog(
        user_id=target_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        performed_by=performed_by,
        ip_address=ip_address,
    )
    db.add(audit)


def log_admin_activity(
    db: Session,
    performed_by: User,
    action: str,
    entity_type: str,
    entity_id: Optional[UUID] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
) -> None:
    if performed_by.role not in (UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.EXECUTIVE):
        return
    activity = AdminActivityLog(
        performed_by_id=performed_by.id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
        ip_address=ip_address,
    )
    db.add(activity)


# ====================== PRIVATE HELPERS ======================
def _get_user_with_relations(db: Session, user_id: UUID) -> User:
    user = (
        db.query(User)
        .options(
            joinedload(User.provider_profile),
            joinedload(User.client_profile),
            joinedload(User.admin_profile),
        )
        .filter(User.id == user_id, User.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ====================== PUBLIC SERVICE FUNCTIONS ======================
def get_user_by_id(db: Session, user_id: UUID, current_user: User) -> User:
    user = _get_user_with_relations(db, user_id)

    if current_user.role == UserRole.SUPER_ADMIN:
        return user
    if current_user.role == UserRole.ADMIN and user.role != UserRole.SUPER_ADMIN:
        return user
    if current_user.role == UserRole.EXECUTIVE and user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    if user.id != current_user.id:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return user


def list_users(
    db: Session,
    current_user: User,
    role: Optional[UserRole] = None,
    account_status: Optional[AccountStatus] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[User], int]:
    if current_user.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")

    query = db.query(User).filter(User.deleted_at.is_(None))

    if role:
        query = query.filter(User.role == role)
    if account_status:
        query = query.filter(User.account_status == account_status)
    if search:
        query = query.filter(
            or_(
                User.full_name.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )

    total = query.count()
    users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
    return users, total

def update_user_basic(
    db: Session, current_user: User, payload: UserUpdateRequest
) -> User:
    """Self-update basic fields"""
    user = _get_user_with_relations(db, current_user.id)

    updated_fields = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(user, field):
            old_value = getattr(user, field)
            setattr(user, field, value)
            updated_fields[field] = {"old": old_value, "new": value}

    user.updated_at = utc_now()

    log_audit(
        db=db,
        action="UPDATE_USER_BASIC",
        entity_type="user",
        entity_id=user.id,
        details={"updated_fields": updated_fields},
        performed_by=current_user.id,
        target_user_id=user.id,
    )

    db.commit()
    db.refresh(user)
    return user


def update_provider_profile(
    db: Session, current_user: User, payload: ProviderProfileUpdateRequest
) -> User:
    """Provider self-profile update"""
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Only providers can update provider profile")

    user = _get_user_with_relations(db, current_user.id)
    if not user.provider_profile:
        raise HTTPException(status_code=404, detail="Provider profile not found")

    updated_fields = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(user.provider_profile, field):
            old_value = getattr(user.provider_profile, field)
            setattr(user.provider_profile, field, value)
            updated_fields[field] = {"old": old_value, "new": value}

    user.provider_profile.updated_at = utc_now()
    user.updated_at = utc_now()

    log_audit(
        db=db,
        action="UPDATE_PROVIDER_PROFILE",
        entity_type="provider_profile",
        entity_id=user.provider_profile.id,
        details=updated_fields,
        performed_by=current_user.id,
        target_user_id=user.id,
    )

    db.commit()
    db.refresh(user)
    return user


def update_client_profile(
    db: Session, current_user: User, payload: ClientProfileUpdateRequest
) -> User:
    """Client self-profile update"""
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Only clients can update client profile")

    user = _get_user_with_relations(db, current_user.id)
    if not user.client_profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    updated_fields = {}
    for field, value in payload.model_dump(exclude_unset=True).items():
        if hasattr(user.client_profile, field):
            old_value = getattr(user.client_profile, field)
            setattr(user.client_profile, field, value)
            updated_fields[field] = {"old": old_value, "new": value}

    user.client_profile.updated_at = utc_now()
    user.updated_at = utc_now()

    log_audit(
        db=db,
        action="UPDATE_CLIENT_PROFILE",
        entity_type="client_profile",
        entity_id=user.client_profile.id,
        details=updated_fields,
        performed_by=current_user.id,
        target_user_id=user.id,
    )

    db.commit()
    db.refresh(user)
    return user


def change_password(
    db: Session, current_user: User, payload: ChangePasswordRequest
) -> User:
    """Secure password change"""
    user = _get_user_with_relations(db, current_user.id)

    if not verify_password(payload.old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    user.hashed_password = get_password_hash(payload.new_password)
    user.password_changed_at = utc_now()
    user.updated_at = utc_now()

    log_audit(
        db=db,
        action="CHANGE_PASSWORD",
        entity_type="user",
        entity_id=user.id,
        details={"password_changed": True},
        performed_by=current_user.id,
        target_user_id=user.id,
    )

    db.commit()
    db.refresh(user)
    return user



def update_user_status(
    db: Session,
    user_id: UUID,
    payload: UserStatusUpdateRequest,
    performed_by: User,
) -> User:
    """Admin-only status management"""
    if performed_by.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")

    user = _get_user_with_relations(db, user_id)

    if user.role == UserRole.SUPER_ADMIN and performed_by.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Cannot modify super admin")

    old_status = user.account_status
    user.account_status = payload.account_status
    user.updated_at = utc_now()

    # General audit
    log_audit(
        db=db,
        action="UPDATE_USER_STATUS",
        entity_type="user",
        entity_id=user.id,
        details={"old_status": old_status.value, "new_status": payload.account_status.value, "notes": payload.notes},
        performed_by=performed_by.id,
        target_user_id=user.id,
    )

    # Admin-specific activity log
    log_admin_activity(
        db=db,
        performed_by=performed_by,
        action="UPDATE_USER_STATUS",
        entity_type="user",
        entity_id=user.id,
        details={"old_status": old_status.value, "new_status": payload.account_status.value, "notes": payload.notes},
    )

    db.commit()
    db.refresh(user)
    return user


def toggle_provider_publish(
    db: Session,
    provider_id: UUID,
    payload: ProviderPublishRequest,
    performed_by: User,
) -> User:
    """Admin-only provider publish control"""
    if performed_by.role not in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        raise HTTPException(status_code=403, detail="Admin access required")

    user = _get_user_with_relations(db, provider_id)
    if user.role != UserRole.PROVIDER or not user.provider_profile:
        raise HTTPException(status_code=400, detail="Not a provider")

    user.provider_profile.is_published = payload.is_published
    user.provider_profile.updated_at = utc_now()
    user.updated_at = utc_now()

    # General audit
    log_audit(
        db=db,
        action="PROVIDER_PUBLISH_TOGGLE",
        entity_type="provider_profile",
        entity_id=user.provider_profile.id,
        details={"is_published": payload.is_published, "reason": payload.reason},
        performed_by=performed_by.id,
        target_user_id=user.id,
    )

    # Admin-specific activity log
    log_admin_activity(
        db=db,
        performed_by=performed_by,
        action="PROVIDER_PUBLISH_TOGGLE",
        entity_type="provider_profile",
        entity_id=user.provider_profile.id,
        details={"is_published": payload.is_published, "reason": payload.reason},
    )

    db.commit()
    db.refresh(user)
    return user
