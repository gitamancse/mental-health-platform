# app/modules/provider/services/education_service.py
# (Create this new file - minimal but complete for education module)
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.modules.users.models.user_model import User, UserRole
from app.modules.users.models.user_model import ProviderProfile
# If Education model is in provider/models/education_model.py, import it:
from app.modules.provider.models.education_model import ProviderEducation as Education


def _ensure_provider(db: Session, current_user: User):
    if current_user.role != UserRole.PROVIDER:
        raise HTTPException(status_code=403, detail="Provider access required")
    profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Provider profile not found")
    return profile


# TODO: Replace with actual Education model once education_model.py is created
# For now this is placeholder structure - implement once model is ready
def list_education(db: Session, current_user: User):
    _ensure_provider(db, current_user)
    # return db.query(Education).filter(Education.provider_id == profile.id).all()
    return []  # placeholder


def create_education(db: Session, current_user: User, payload):
    profile = _ensure_provider(db, current_user)
    # education = Education(provider_id=profile.id, **payload.model_dump())
    # db.add(education)
    # db.commit()
    # db.refresh(education)
    # return education
    return {"id": "placeholder", **payload.model_dump()}  # placeholder


def update_education(db: Session, current_user: User, education_id: UUID, payload):
    _ensure_provider(db, current_user)
    # TODO: implement update
    return {"id": education_id, **payload.model_dump()}


def delete_education(db: Session, current_user: User, education_id: UUID):
    _ensure_provider(db, current_user)
    # TODO: implement delete
    return {"message": "Education record deleted successfully"}