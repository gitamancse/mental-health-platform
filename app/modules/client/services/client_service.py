# app/modules/client/services/client_service.py
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.modules.users.models.user_model import User, UserRole, ClientProfile
from app.modules.client.models.client_model import (
    ClientAssessment, ClientIntakeForm, ClientAppointment,
    ClientSubscription, ClientGoal, ClientProgress,
    ClientJournalEntry, ClientMedicalHistory, ClientMedication,
    ClientAllergy, ClientPreference, ClientConsent, ClientDocument
)

from app.modules.client.schemas.client_schema import (
    ClientDocumentCreateRequest,ClientAppointmentCreateRequest,
    ClientAssessmentCreateRequest, ClientGoalCreateRequest,
    ClientJournalCreateRequest,ClientMedicalHistoryUpdateRequest,
    ClientPreferenceUpdateRequest, 
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ====================== PRIVATE HELPER ======================
def _ensure_client(db: Session, current_user: User) -> ClientProfile:
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Client access required")

    profile = db.query(ClientProfile).filter(
        ClientProfile.user_id == current_user.id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Client profile not found")

    return profile


# ====================== DASHBOARD ======================
def get_client_dashboard(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)

    # TODO: Replace with real queries once sessions/appointments are fully integrated
    upcoming = []   # join with ClientAppointment + Provider
    recent_assessments = db.query(ClientAssessment).filter(
        ClientAssessment.client_id == profile.id
    ).order_by(ClientAssessment.taken_at.desc()).limit(3).all()

    subscription = db.query(ClientSubscription).filter(
        ClientSubscription.client_id == profile.id
    ).first()

    pending_consents = db.query(ClientConsent).filter(
        ClientConsent.client_id == profile.id,
        ClientConsent.accepted == False
    ).count()

    return {
        "profile": profile,
        "upcoming_appointments": upcoming,
        "recent_assessments": recent_assessments,
        "active_subscription": subscription,
        "pending_consents": pending_consents,
        "streak_days": 0,  # can be calculated from journal entries later
    }


# ====================== ASSESSMENTS ======================
def create_self_assessment(db: Session, current_user: User, payload: ClientAssessmentCreateRequest):
    profile = _ensure_client(db, current_user)

    assessment = ClientAssessment(
        client_id=profile.id,
        **payload.model_dump()
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return assessment


def list_assessments(db: Session, current_user: User, skip: int = 0, limit: int = 20):
    profile = _ensure_client(db, current_user)
    return db.query(ClientAssessment).filter(
        ClientAssessment.client_id == profile.id
    ).order_by(ClientAssessment.taken_at.desc()).offset(skip).limit(limit).all()


def list_intake_forms(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    return db.query(ClientIntakeForm).filter(
        ClientIntakeForm.client_id == profile.id
    ).order_by(ClientIntakeForm.completed_at.desc()).all()


# ====================== APPOINTMENTS ======================
def list_appointments(db: Session, current_user: User, status: Optional[str] = None):
    profile = _ensure_client(db, current_user)
    query = db.query(ClientAppointment).filter(
        ClientAppointment.client_id == profile.id
    )
    if status:
        query = query.filter(ClientAppointment.status == status)
    return query.order_by(ClientAppointment.appointment_datetime).all()


def request_appointment(db: Session, current_user: User, payload: ClientAppointmentCreateRequest):
    profile = _ensure_client(db, current_user)

    appointment = ClientAppointment(
        client_id=profile.id,
        status="REQUESTED",
        **payload.model_dump()
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, current_user: User, appointment_id: UUID):
    profile = _ensure_client(db, current_user)

    appointment = db.query(ClientAppointment).filter(
        ClientAppointment.id == appointment_id,
        ClientAppointment.client_id == profile.id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status not in ("SCHEDULED", "REQUESTED"):
        raise HTTPException(status_code=400, detail="Cannot cancel this appointment")

    appointment.status = "CANCELLED"
    db.commit()
    return {"message": "Appointment cancelled successfully"}


# ====================== SUBSCRIPTION ======================
def get_subscription(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    sub = db.query(ClientSubscription).filter(
        ClientSubscription.client_id == profile.id
    ).first()
    if not sub:
        raise HTTPException(status_code=404, detail="No active subscription found")
    return sub


# ====================== GOALS & PROGRESS ======================
def list_goals(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    return db.query(ClientGoal).filter(
        ClientGoal.client_id == profile.id
    ).order_by(ClientGoal.created_at.desc()).all()


def create_goal(db: Session, current_user: User, payload: ClientGoalCreateRequest):
    profile = _ensure_client(db, current_user)
    goal = ClientGoal(client_id=profile.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def add_progress(db: Session, current_user: User, goal_id: UUID, progress_percentage: float, notes: Optional[str]):
    profile = _ensure_client(db, current_user)

    progress = ClientProgress(
        client_id=profile.id,
        goal_id=goal_id,
        progress_percentage=progress_percentage,
        notes=notes
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


# ====================== JOURNAL ======================
def list_journal_entries(db: Session, current_user: User, skip: int = 0, limit: int = 20):
    profile = _ensure_client(db, current_user)
    return db.query(ClientJournalEntry).filter(
        ClientJournalEntry.client_id == profile.id
    ).order_by(ClientJournalEntry.created_at.desc()).offset(skip).limit(limit).all()


def create_journal_entry(db: Session, current_user: User, payload: ClientJournalCreateRequest):
    profile = _ensure_client(db, current_user)
    entry = ClientJournalEntry(client_id=profile.id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


# ====================== MEDICAL & HEALTH ======================
def get_medical_history(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    return db.query(ClientMedicalHistory).filter(
        ClientMedicalHistory.client_id == profile.id
    ).first() or ClientMedicalHistory(client_id=profile.id)


def update_medical_history(db: Session, current_user: User, payload: ClientMedicalHistoryUpdateRequest):
    profile = _ensure_client(db, current_user)

    history = db.query(ClientMedicalHistory).filter(
        ClientMedicalHistory.client_id == profile.id
    ).first()

    if not history:
        history = ClientMedicalHistory(client_id=profile.id)
        db.add(history)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(history, field, value)

    history.last_updated_at = utc_now()
    db.commit()
    db.refresh(history)
    return history


def list_medications(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    return db.query(ClientMedication).filter(
        ClientMedication.client_id == profile.id
    ).all()


def list_allergies(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    return db.query(ClientAllergy).filter(
        ClientAllergy.client_id == profile.id
    ).all()


# ====================== PREFERENCES & CONSENTS ======================
def get_preferences(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    pref = db.query(ClientPreference).filter(
        ClientPreference.client_id == profile.id
    ).first()
    return pref or ClientPreference(client_id=profile.id)


def update_preferences(db: Session, current_user: User, payload: ClientPreferenceUpdateRequest):
    profile = _ensure_client(db, current_user)

    pref = db.query(ClientPreference).filter(
        ClientPreference.client_id == profile.id
    ).first()

    if not pref:
        pref = ClientPreference(client_id=profile.id)
        db.add(pref)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(pref, field, value)

    db.commit()
    db.refresh(pref)
    return pref


def list_consents(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    return db.query(ClientConsent).filter(
        ClientConsent.client_id == profile.id
    ).order_by(ClientConsent.accepted_at.desc()).all()


# ====================== DOCUMENTS ======================
def list_documents(db: Session, current_user: User):
    profile = _ensure_client(db, current_user)
    return db.query(ClientDocument).filter(
        ClientDocument.client_id == profile.id
    ).order_by(ClientDocument.uploaded_at.desc()).all()


def upload_document(db: Session, current_user: User, payload: ClientDocumentCreateRequest):
    profile = _ensure_client(db, current_user)

    doc = ClientDocument(
        client_id=profile.id,
        **payload.model_dump()
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, current_user: User, document_id: UUID):
    profile = _ensure_client(db, current_user)

    doc = db.query(ClientDocument).filter(
        ClientDocument.id == document_id,
        ClientDocument.client_id == profile.id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}