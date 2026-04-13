# app/modules/users/routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.dependencies import get_db, get_current_user, get_current_super_admin
from app.modules.users.models.user_model import User, UserRole
from app.modules.users.schemas.user_schema import (
    UserUpdateRequest,
    ProviderProfileUpdateRequest,
    ClientProfileUpdateRequest,
    ChangePasswordRequest,
    UserStatusUpdateRequest,
    ProviderPublishRequest,
    UserListResponse,
    UserDetailResponse,
    UserSummaryResponse,
    ProviderLicenseResponse,
    LicenseCreate,
    MessageResponse,
)
from app.modules.users.services.user_service import (
    get_user_by_id,
    list_users,
    update_user_basic,
    update_provider_profile,
    update_client_profile,
    change_password,
    add_provider_license,
    update_user_status,
    toggle_provider_publish,
)

user_router = APIRouter(prefix="/users", tags=["Users"])


# ====================== SELF ENDPOINTS ======================
@user_router.get("/me", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full profile of currently logged-in user"""
    return get_user_by_id(db, current_user.id, current_user)


@user_router.put("/me", response_model=UserDetailResponse)
def update_me(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update basic user information"""
    return update_user_basic(db, current_user, payload)


@user_router.put("/me/provider-profile", response_model=UserDetailResponse)
def update_my_provider_profile(
    payload: ProviderProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Provider-only profile update"""
    return update_provider_profile(db, current_user, payload)


@user_router.put("/me/client-profile", response_model=UserDetailResponse)
def update_my_client_profile(
    payload: ClientProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Client-only profile update"""
    return update_client_profile(db, current_user, payload)


@user_router.post("/me/change-password", response_model=MessageResponse)
def update_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Secure password change (requires old password)"""
    change_password(db, current_user, payload)
    return {"message": "Password updated successfully"}


@user_router.post("/me/licenses", response_model=ProviderLicenseResponse)
def add_license(
    payload: LicenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Providers can add additional licenses"""
    return add_provider_license(db, current_user, payload)


# ====================== ADMIN-ONLY ENDPOINTS ======================
@user_router.get("/", response_model=UserListResponse)
def list_users_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role: Optional[UserRole] = Query(None),
    account_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Paginated user list (Admin + Super Admin only)"""
    users, total = list_users(
        db=db,
        current_user=current_user,
        role=role,
        account_status=account_status,
        search=search,
        skip=skip,
        limit=limit,
    )

    return {
        "total": total,
        "items": users,
        "page": (skip // limit) + 1 if limit else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


@user_router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get any user with full details"""
    return get_user_by_id(db, user_id, current_user)


@user_router.put("/{user_id}/status", response_model=UserDetailResponse)
def update_user_status_endpoint(
    user_id: UUID,
    payload: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """Update user status (suspension, activation, etc.)"""
    return update_user_status(db, user_id, payload, current_user)


@user_router.put("/{user_id}/publish", response_model=UserDetailResponse)
def toggle_provider_publish_endpoint(
    user_id: UUID,
    payload: ProviderPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """Toggle provider visibility in the marketplace"""
    return toggle_provider_publish(db, user_id, payload, current_user)

# app/modules/users/routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID

from app.core.dependencies import get_db, get_current_user, get_current_super_admin
from app.modules.users.models.user_model import User, UserRole
from app.modules.users.schemas.user_schema import (
    UserUpdateRequest,
    ProviderProfileUpdateRequest,
    ClientProfileUpdateRequest,
    ChangePasswordRequest,
    UserStatusUpdateRequest,
    ProviderPublishRequest,
    UserListResponse,
    UserDetailResponse,
    UserSummaryResponse,
    ProviderLicenseResponse,
    LicenseCreate,
    MessageResponse,
)
from app.modules.users.services.user_service import (
    get_user_by_id,
    list_users,
    update_user_basic,
    update_provider_profile,
    update_client_profile,
    change_password,
    add_provider_license,
    update_user_status,
    toggle_provider_publish,
)

user_router = APIRouter(prefix="/users", tags=["Users"])


# ====================== SELF ENDPOINTS ======================
@user_router.get("/me", response_model=UserDetailResponse, status_code=status.HTTP_200_OK)
def get_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full profile of currently logged-in user"""
    return get_user_by_id(db, current_user.id, current_user)


@user_router.put("/me", response_model=UserDetailResponse)
def update_me(
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update basic user information"""
    return update_user_basic(db, current_user, payload)


@user_router.put("/me/provider-profile", response_model=UserDetailResponse)
def update_my_provider_profile(
    payload: ProviderProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Provider-only profile update"""
    return update_provider_profile(db, current_user, payload)


@user_router.put("/me/client-profile", response_model=UserDetailResponse)
def update_my_client_profile(
    payload: ClientProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Client-only profile update"""
    return update_client_profile(db, current_user, payload)


@user_router.post("/me/change-password", response_model=MessageResponse)
def update_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Secure password change (requires old password)"""
    change_password(db, current_user, payload)
    return {"message": "Password updated successfully"}


@user_router.post("/me/licenses", response_model=ProviderLicenseResponse)
def add_license(
    payload: LicenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Providers can add additional licenses"""
    return add_provider_license(db, current_user, payload)


# ====================== ADMIN-ONLY ENDPOINTS ======================
@user_router.get("/", response_model=UserListResponse)
def list_users_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    role: Optional[UserRole] = Query(None),
    account_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """Paginated user list (Admin + Super Admin only)"""
    users, total = list_users(
        db=db,
        current_user=current_user,
        role=role,
        account_status=account_status,
        search=search,
        skip=skip,
        limit=limit,
    )

    return {
        "total": total,
        "items": users,
        "page": (skip // limit) + 1 if limit else 1,
        "size": limit,
        "pages": (total + limit - 1) // limit if limit else 1,
    }


@user_router.get("/{user_id}", response_model=UserDetailResponse)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get any user with full details"""
    return get_user_by_id(db, user_id, current_user)


@user_router.put("/{user_id}/status", response_model=UserDetailResponse)
def update_user_status_endpoint(
    user_id: UUID,
    payload: UserStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """Update user status (suspension, activation, etc.)"""
    return update_user_status(db, user_id, payload, current_user)


@user_router.put("/{user_id}/publish", response_model=UserDetailResponse)
def toggle_provider_publish_endpoint(
    user_id: UUID,
    payload: ProviderPublishRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_super_admin),
):
    """Toggle provider visibility in the marketplace"""
    return toggle_provider_publish(db, user_id, payload, current_user)

# ====================== EXECUTIVE ENDPOINTS (Future) ======================
# These will be expanded once organization scoping is fully implemented