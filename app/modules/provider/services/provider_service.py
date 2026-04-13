# app/modules/provider/services/provider_service.py
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.modules.users.models.user_model import User, UserRole, ProviderProfile
from app.modules.provider.models.provider_model import (
    ProviderAvailability, ProviderBlockedTime, ProviderGallery,
    ProviderPublicationRequest, ProviderWaitlist, ProviderReview,
    ProviderSubscription
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ====================== PRIVATE HELPERS ======================
def _ensure_provider(db: Session, current_user: User) -> ProviderProfile:
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Provider access required")

    profile = db.query(ProviderProfile).filter(
        ProviderProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Provider profile not found. Please complete registration first.")

    return profile


# ====================== DASHBOARD ======================
def get_provider_dashboard(db: Session, current_user: User):
    profile = _ensure_provider(db, current_user)

    # TODO: Replace with real queries once sessions module is integrated
    total_today = 0  # db.query(...).filter(...).count()
    upcoming = []    # join with sessions
    this_month = 0
    avg_rating = profile.average_rating or 0.0

    pub_status = "NOT_REQUESTED"
    pub_req = db.query(ProviderPublicationRequest).filter(
        ProviderPublicationRequest.provider_id == profile.id
    ).order_by(ProviderPublicationRequest.requested_at.desc()).first()
    if pub_req:
        pub_status = pub_req.status

    subscription = db.query(ProviderSubscription).filter(
        ProviderSubscription.provider_id == profile.id
    ).first()

    return {
        "total_appointments_today": total_today,
        "upcoming_sessions": upcoming,
        "total_sessions_this_month": this_month,
        "average_rating": avg_rating,
        "profile": profile,
        "publication_status": pub_status,
        "subscription": subscription,
    }


# ====================== AVAILABILITY ======================
def list_availability(db: Session, current_user: User) -> List[dict]:
    profile = _ensure_provider(db, current_user)
    items = db.query(ProviderAvailability).filter(
        ProviderAvailability.provider_id == profile.id
    ).order_by(ProviderAvailability.day_of_week, ProviderAvailability.start_time).all()
    return items


def create_availability(db: Session, current_user: User, payload):
    profile = _ensure_provider(db, current_user)

    # Optional: prevent overlapping slots (future enhancement)
    avail = ProviderAvailability(
        provider_id=profile.id,
        **payload.model_dump()
    )
    db.add(avail)
    db.commit()
    db.refresh(avail)
    return avail


def update_availability(db: Session, current_user: User, availability_id: UUID, payload):
    profile = _ensure_provider(db, current_user)

    avail = db.query(ProviderAvailability).filter(
        ProviderAvailability.id == availability_id,
        ProviderAvailability.provider_id == profile.id
    ).first()
    if not avail:
        raise HTTPException(status_code=404, detail="Availability slot not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(avail, field, value)

    db.commit()
    db.refresh(avail)
    return avail


def delete_availability(db: Session, current_user: User, availability_id: UUID):
    profile = _ensure_provider(db, current_user)

    avail = db.query(ProviderAvailability).filter(
        ProviderAvailability.id == availability_id,
        ProviderAvailability.provider_id == profile.id
    ).first()
    if not avail:
        raise HTTPException(status_code=404, detail="Availability slot not found")

    db.delete(avail)
    db.commit()
    return {"message": "Availability slot deleted successfully"}


# ====================== BLOCKED TIMES ======================
def list_blocked_times(db: Session, current_user: User, start_date: Optional[datetime], end_date: Optional[datetime]):
    profile = _ensure_provider(db, current_user)

    query = db.query(ProviderBlockedTime).filter(
        ProviderBlockedTime.provider_id == profile.id
    )
    if start_date:
        query = query.filter(ProviderBlockedTime.start_datetime >= start_date)
    if end_date:
        query = query.filter(ProviderBlockedTime.end_datetime <= end_date)

    return query.order_by(ProviderBlockedTime.start_datetime).all()


def create_blocked_time(db: Session, current_user: User, payload):
    profile = _ensure_provider(db, current_user)

    blocked = ProviderBlockedTime(
        provider_id=profile.id,
        **payload.model_dump()
    )
    db.add(blocked)
    db.commit()
    db.refresh(blocked)
    return blocked


def delete_blocked_time(db: Session, current_user: User, blocked_id: UUID):
    profile = _ensure_provider(db, current_user)

    blocked = db.query(ProviderBlockedTime).filter(
        ProviderBlockedTime.id == blocked_id,
        ProviderBlockedTime.provider_id == profile.id
    ).first()
    if not blocked:
        raise HTTPException(status_code=404, detail="Blocked time not found")

    db.delete(blocked)
    db.commit()
    return {"message": "Blocked time deleted successfully"}


# ====================== GALLERY ======================
def list_gallery(db: Session, current_user: User):
    profile = _ensure_provider(db, current_user)
    return db.query(ProviderGallery).filter(
        ProviderGallery.provider_id == profile.id
    ).order_by(ProviderGallery.uploaded_at.desc()).all()


def add_to_gallery(db: Session, current_user: User, payload):
    profile = _ensure_provider(db, current_user)

    gallery = ProviderGallery(
        provider_id=profile.id,
        **payload.model_dump()
    )
    db.add(gallery)
    db.commit()
    db.refresh(gallery)
    return gallery


def delete_gallery_item(db: Session, current_user: User, gallery_id: UUID):
    profile = _ensure_provider(db, current_user)

    item = db.query(ProviderGallery).filter(
        ProviderGallery.id == gallery_id,
        ProviderGallery.provider_id == profile.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Gallery item not found")

    db.delete(item)
    db.commit()
    return {"message": "Gallery item removed successfully"}


# ====================== PUBLICATION ======================
def request_publication(db: Session, current_user: User):
    profile = _ensure_provider(db, current_user)

    # Check if already published or pending
    existing = db.query(ProviderPublicationRequest).filter(
        ProviderPublicationRequest.provider_id == profile.id,
        ProviderPublicationRequest.status.in_(["PENDING", "APPROVED"])
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Publication request already exists or is approved")

    req = ProviderPublicationRequest(provider_id=profile.id)
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_publication_status(db: Session, current_user: User):
    profile = _ensure_provider(db, current_user)

    req = db.query(ProviderPublicationRequest).filter(
        ProviderPublicationRequest.provider_id == profile.id
    ).order_by(ProviderPublicationRequest.requested_at.desc()).first()

    if not req:
        return {"id": None, "status": "NOT_REQUESTED", "requested_at": None}
    return req


# ====================== WAITLIST ======================
def get_waitlist(db: Session, current_user: User, skip: int = 0, limit: int = 20):
    profile = _ensure_provider(db, current_user)

    query = db.query(ProviderWaitlist).join(User, ProviderWaitlist.client_id == User.id).filter(
        ProviderWaitlist.provider_id == profile.id
    ).options(joinedload(ProviderWaitlist.client))

    total = query.count()  # not used for list but available
    items = query.order_by(ProviderWaitlist.requested_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": w.id,
            "client_id": w.client_id,
            "client_name": w.client.full_name,
            "requested_at": w.requested_at,
            "notes": w.notes,
        }
        for w in items
    ]


# ====================== REVIEWS ======================
def get_reviews(db: Session, current_user: User, skip: int = 0, limit: int = 20):
    profile = _ensure_provider(db, current_user)

    query = db.query(ProviderReview).join(User, ProviderReview.client_id == User.id).filter(
        ProviderReview.provider_id == profile.id
    ).options(joinedload(ProviderReview.client))

    items = query.order_by(ProviderReview.created_at.desc()).offset(skip).limit(limit).all()

    return [
        {
            "id": r.id,
            "client_id": r.client_id,
            "client_name": r.client.full_name,
            "rating": r.rating,
            "comment": r.comment,
            "session_id": r.session_id,
            "created_at": r.created_at,
        }
        for r in items
    ]


# ====================== SUBSCRIPTION ======================
def get_subscription(db: Session, current_user: User):
    profile = _ensure_provider(db, current_user)

    sub = db.query(ProviderSubscription).filter(
        ProviderSubscription.provider_id == profile.id
    ).first()

    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found. Contact support.")
    return sub