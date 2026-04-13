# app/modules/provider/routers/provider_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.core.dependencies import get_db, get_current_user
from app.modules.users.models.user_model import User, UserRole
from app.modules.provider.models.provider_model import (
    ProviderAvailability, ProviderBlockedTime, ProviderGallery,
    ProviderPublicationRequest, ProviderWaitlist, ProviderReview,
    ProviderSubscription
)
from app.modules.provider.schemas.provider_schema import (
    ProviderAvailabilityCreateRequest,
    ProviderAvailabilityUpdateRequest,
    ProviderBlockedTimeCreateRequest,
    ProviderGalleryCreateRequest,
    ProviderPublicationRequestResponse,
    ProviderWaitlistResponse,
    ProviderReviewResponse,
    ProviderSubscriptionResponse,
    ProviderDashboardResponse,
    MessageResponse,
    ProviderAvailabilityResponse,
    ProviderBlockedTimeResponse,
    ProviderGalleryResponse,
)
from app.modules.provider.services.provider_service import (
    get_provider_dashboard,
    list_availability,
    create_availability,
    update_availability,
    delete_availability,
    list_blocked_times,
    create_blocked_time,
    delete_blocked_time,
    list_gallery,
    add_to_gallery,
    delete_gallery_item,
    request_publication,
    get_publication_status,
    get_waitlist,
    get_reviews,
    get_subscription,
)

provider_router = APIRouter(prefix="/providers", tags=["Providers"])


# ====================== SELF DASHBOARD ======================
@provider_router.get("/me/dashboard", response_model=ProviderDashboardResponse)
def get_provider_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Provider dashboard - key metrics and quick view"""
    return get_provider_dashboard(db, current_user)


# ====================== AVAILABILITY (TIME SLOTS) ======================
@provider_router.get("/me/availability", response_model=List[ProviderAvailabilityResponse])
def list_my_availability(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all availability slots (recurring weekly schedule)"""
    return list_availability(db, current_user)


@provider_router.post("/me/availability", response_model=ProviderAvailabilityResponse, status_code=status.HTTP_201_CREATED)
def create_my_availability(
    payload: ProviderAvailabilityCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a new availability slot"""
    return create_availability(db, current_user, payload)


@provider_router.put("/me/availability/{availability_id}", response_model=ProviderAvailabilityResponse)
def update_my_availability(
    availability_id: UUID,
    payload: ProviderAvailabilityUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an availability slot"""
    return update_availability(db, current_user, availability_id, payload)


@provider_router.delete("/me/availability/{availability_id}", response_model=MessageResponse)
def delete_my_availability(
    availability_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an availability slot"""
    return delete_availability(db, current_user, availability_id)


# ====================== BLOCKED TIMES / HOLIDAYS ======================
@provider_router.get("/me/blocked-times", response_model=List[ProviderBlockedTimeResponse])
def list_my_blocked_times(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """List blocked times / holidays"""
    return list_blocked_times(db, current_user, start_date, end_date)


@provider_router.post("/me/blocked-times", response_model=ProviderBlockedTimeResponse, status_code=status.HTTP_201_CREATED)
def create_my_blocked_time(
    payload: ProviderBlockedTimeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Block a specific date/time range (holiday, vacation, etc.)"""
    return create_blocked_time(db, current_user, payload)


@provider_router.delete("/me/blocked-times/{blocked_id}", response_model=MessageResponse)
def delete_my_blocked_time(
    blocked_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a blocked time entry"""
    return delete_blocked_time(db, current_user, blocked_id)


# ====================== GALLERY (PHOTOS / VIDEOS FOR PROFILE) ======================
@provider_router.get("/me/gallery", response_model=List[ProviderGalleryResponse])
def list_my_gallery(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all gallery items"""
    return list_gallery(db, current_user)


@provider_router.post("/me/gallery", response_model=ProviderGalleryResponse, status_code=status.HTTP_201_CREATED)
def add_to_my_gallery(
    file_url: str,   # In production: use UploadFile + file_storage utility
    caption: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add photo/video to provider gallery (public profile)"""
    payload = ProviderGalleryCreateRequest(file_url=file_url, file_type="image", caption=caption)
    return add_to_gallery(db, current_user, payload)


@provider_router.delete("/me/gallery/{gallery_id}", response_model=MessageResponse)
def delete_my_gallery_item(
    gallery_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Remove gallery item"""
    return delete_gallery_item(db, current_user, gallery_id)


# ====================== PUBLICATION / MARKETPLACE VISIBILITY ======================
@provider_router.post("/me/publication-request", response_model=ProviderPublicationRequestResponse, status_code=status.HTTP_201_CREATED)
def request_publication_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request to be published in the provider directory (admin approval required)"""
    return request_publication(db, current_user)


@provider_router.get("/me/publication-status", response_model=ProviderPublicationRequestResponse)
def get_my_publication_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Check current publication request status"""
    return get_publication_status(db, current_user)


# ====================== WAITLIST ======================
@provider_router.get("/me/waitlist", response_model=List[ProviderWaitlistResponse])
def get_my_waitlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """View clients who joined my waitlist"""
    return get_waitlist(db, current_user, skip, limit)


# ====================== REVIEWS ======================
@provider_router.get("/me/reviews", response_model=List[ProviderReviewResponse])
def get_my_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """View all reviews received"""
    return get_reviews(db, current_user, skip, limit)


# ====================== SUBSCRIPTION ======================
@provider_router.get("/me/subscription", response_model=ProviderSubscriptionResponse)
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View current subscription tier and status"""
    return get_subscription(db, current_user)