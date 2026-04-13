# app/modules/provider/routers/education_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.modules.users.models.user_model import User, UserRole
from app.modules.provider.schemas.education_schema import EducationCreate, EducationResponse
from app.modules.provider.services.education_service import (  # we'll create this below
    list_education,
    create_education,
    update_education,
    delete_education,
)

education_router = APIRouter(prefix="/provider/education", tags=["Provider Education"])


@education_router.get("/", response_model=List[EducationResponse])
def list_my_education(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all education / CE entries for the provider"""
    return list_education(db, current_user)


@education_router.post("/", response_model=EducationResponse, status_code=status.HTTP_201_CREATED)
def create_my_education(
    payload: EducationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add new degree / continuing education record"""
    return create_education(db, current_user, payload)


@education_router.put("/{education_id}", response_model=EducationResponse)
def update_my_education(
    education_id: UUID,
    payload: EducationCreate,  # reuse create for simplicity (or create Update schema)
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update education record"""
    return update_education(db, current_user, education_id, payload)


@education_router.delete("/{education_id}", response_model=dict)
def delete_my_education(
    education_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete education record"""
    return delete_education(db, current_user, education_id)