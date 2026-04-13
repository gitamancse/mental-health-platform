# app/modules/client/routers/client_router.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.dependencies import get_db, get_current_user
from app.modules.users.models.user_model import User, UserRole
from app.modules.client.schemas.client_schema import (
    ClientDashboardResponse,
    ClientAssessmentCreateRequest,
    ClientSelfAssessmentResponse,
    ClientIntakeFormResponse,
    ClientAppointmentResponse,
    ClientAppointmentCreateRequest,
    ClientSubscriptionResponse,
    ClientGoalResponse,
    ClientGoalCreateRequest,
    ClientProgressResponse,
    ClientJournalEntryResponse,
    ClientJournalCreateRequest,
    ClientMedicalHistoryResponse,
    ClientMedicalHistoryUpdateRequest,
    ClientMedicationResponse,
    ClientAllergyResponse,
    ClientPreferenceResponse,
    ClientPreferenceUpdateRequest,
    ClientConsentResponse,
    ClientDocumentResponse,
    ClientDocumentCreateRequest,
    MessageResponse,
)
from app.modules.client.services.client_service import (
    get_client_dashboard,
    create_self_assessment,
    list_assessments,
    list_intake_forms,
    list_appointments,
    request_appointment,
    cancel_appointment,
    get_subscription,
    list_goals,
    create_goal,
    add_progress,
    list_journal_entries,
    create_journal_entry,
    get_medical_history,
    update_medical_history,
    list_medications,
    list_allergies,
    get_preferences,
    update_preferences,
    list_consents,
    list_documents,
    upload_document,
    delete_document,
)

client_router = APIRouter(prefix="/clients", tags=["Clients"])


# ====================== DASHBOARD ======================
@client_router.get("/me/dashboard", response_model=ClientDashboardResponse)
def get_client_dashboard_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Client personal dashboard"""
    return get_client_dashboard(db, current_user)


# ====================== SELF-ASSESSMENT & INTAKE ======================
@client_router.post("/me/assessments", response_model=ClientSelfAssessmentResponse, status_code=status.HTTP_201_CREATED)
def create_assessment(
    payload: ClientAssessmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Take a self-assessment (PHQ-9, GAD-7, etc.)"""
    return create_self_assessment(db, current_user, payload)


@client_router.get("/me/assessments", response_model=List[ClientSelfAssessmentResponse])
def get_my_assessments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List all my self-assessments"""
    return list_assessments(db, current_user, skip, limit)


@client_router.get("/me/intake-forms", response_model=List[ClientIntakeFormResponse])
def get_my_intake_forms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List completed intake forms"""
    return list_intake_forms(db, current_user)


# ====================== APPOINTMENTS ======================
@client_router.get("/me/appointments", response_model=List[ClientAppointmentResponse])
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = Query(None),
):
    """List my appointments"""
    return list_appointments(db, current_user, status)


@client_router.post("/me/appointments", response_model=ClientAppointmentResponse, status_code=status.HTTP_201_CREATED)
def request_appointment_endpoint(
    payload: ClientAppointmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Request a new appointment with a provider"""
    return request_appointment(db, current_user, payload)


@client_router.delete("/me/appointments/{appointment_id}", response_model=MessageResponse)
def cancel_appointment_endpoint(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an upcoming appointment"""
    return cancel_appointment(db, current_user, appointment_id)


# ====================== SUBSCRIPTION ======================
@client_router.get("/me/subscription", response_model=ClientSubscriptionResponse)
def get_my_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View my current membership/subscription"""
    return get_subscription(db, current_user)


# ====================== GOALS & PROGRESS ======================
@client_router.get("/me/goals", response_model=List[ClientGoalResponse])
def get_my_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List my therapy goals"""
    return list_goals(db, current_user)


@client_router.post("/me/goals", response_model=ClientGoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal_endpoint(
    payload: ClientGoalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new therapy goal"""
    return create_goal(db, current_user, payload)


@client_router.post("/me/goals/{goal_id}/progress", response_model=ClientProgressResponse, status_code=status.HTTP_201_CREATED)
def add_goal_progress(
    goal_id: UUID,
    progress_percentage: float = Query(..., ge=0, le=100),
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record progress on a goal"""
    return add_progress(db, current_user, goal_id, progress_percentage, notes)


# ====================== JOURNAL ======================
@client_router.get("/me/journal", response_model=List[ClientJournalEntryResponse])
def get_my_journal(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """List my journal entries"""
    return list_journal_entries(db, current_user, skip, limit)


@client_router.post("/me/journal", response_model=ClientJournalEntryResponse, status_code=status.HTTP_201_CREATED)
def create_journal_entry_endpoint(
    payload: ClientJournalCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new journal entry"""
    return create_journal_entry(db, current_user, payload)


# ====================== MEDICAL & HEALTH ======================
@client_router.get("/me/medical-history", response_model=ClientMedicalHistoryResponse)
def get_medical_history_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View / update medical history"""
    return get_medical_history(db, current_user)


@client_router.put("/me/medical-history", response_model=ClientMedicalHistoryResponse)
def update_medical_history_endpoint(
    payload: ClientMedicalHistoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update medical history"""
    return update_medical_history(db, current_user, payload)


@client_router.get("/me/medications", response_model=List[ClientMedicationResponse])
def get_medications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List my medications"""
    return list_medications(db, current_user)


@client_router.get("/me/allergies", response_model=List[ClientAllergyResponse])
def get_allergies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List my allergies"""
    return list_allergies(db, current_user)


# ====================== PREFERENCES & CONSENTS ======================
@client_router.get("/me/preferences", response_model=ClientPreferenceResponse)
def get_preferences_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View my notification & communication preferences"""
    return get_preferences(db, current_user)


@client_router.put("/me/preferences", response_model=ClientPreferenceResponse)
def update_preferences_endpoint(
    payload: ClientPreferenceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update my preferences"""
    return update_preferences(db, current_user, payload)


@client_router.get("/me/consents", response_model=List[ClientConsentResponse])
def get_consents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all my signed consents"""
    return list_consents(db, current_user)


# ====================== DOCUMENTS ======================
@client_router.get("/me/documents", response_model=List[ClientDocumentResponse])
def get_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List my uploaded documents"""
    return list_documents(db, current_user)


@client_router.post("/me/documents", response_model=ClientDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document_endpoint(
    payload: ClientDocumentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a new document (medical records, ID, etc.)"""
    return upload_document(db, current_user, payload)


@client_router.delete("/me/documents/{document_id}", response_model=MessageResponse)
def delete_document_endpoint(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document"""
    return delete_document(db, current_user, document_id)