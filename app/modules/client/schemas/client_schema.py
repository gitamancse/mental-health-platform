# # app/modules/client/schemas/client_schema.py
# from datetime import datetime
# from typing import Optional, List
# from uuid import UUID

# from pydantic import BaseModel, Field, ConfigDict, HttpUrl

# from app.modules.users.schemas.user_schema import ClientProfileResponse


# # ====================== DASHBOARD ======================
# class ClientAppointmentSummary(BaseModel):
#     id: UUID
#     provider_name: str
#     provider_title: str
#     appointment_datetime: datetime
#     status: str

#     model_config = ConfigDict(from_attributes=True)


# class ClientDashboardResponse(BaseModel):
#     profile: ClientProfileResponse
#     upcoming_appointments: List[ClientAppointmentSummary]
#     recent_assessments: List["ClientSelfAssessmentResponse"]
#     active_subscription: Optional["ClientSubscriptionResponse"] = None
#     pending_consents: int
#     streak_days: int = 0

#     model_config = ConfigDict(from_attributes=True)


# # ====================== SELF-ASSESSMENT & INTAKE ======================
# class ClientSelfAssessmentResponse(BaseModel):
#     id: UUID
#     assessment_type: str
#     score: int
#     responses: Optional[dict] = None
#     taken_at: datetime

#     model_config = ConfigDict(from_attributes=True)


# class ClientAssessmentCreateRequest(BaseModel):
#     assessment_type: str = Field(..., pattern="^(phq9|gad7|initial_intake|other)$")
#     score: int = Field(..., ge=0)
#     responses: Optional[dict] = None

#     model_config = ConfigDict(extra="forbid")


# class ClientIntakeFormResponse(BaseModel):
#     id: UUID
#     form_type: str
#     responses: dict
#     completed_at: datetime

#     model_config = ConfigDict(from_attributes=True)


# # ====================== APPOINTMENTS ======================
# class ClientAppointmentResponse(BaseModel):
#     id: UUID
#     provider_id: UUID
#     provider_name: str
#     appointment_datetime: datetime
#     status: str
#     notes: Optional[str] = None

#     model_config = ConfigDict(from_attributes=True)


# class ClientAppointmentCreateRequest(BaseModel):
#     provider_id: UUID
#     preferred_datetime: datetime
#     notes: Optional[str] = Field(None, max_length=1000)

#     model_config = ConfigDict(extra="forbid")


# # ====================== SUBSCRIPTION ======================
# class ClientSubscriptionResponse(BaseModel):
#     id: UUID
#     plan_name: str
#     status: str
#     expiry_date: Optional[datetime] = None
#     auto_renew: bool

#     model_config = ConfigDict(from_attributes=True)


# # ====================== GOALS & PROGRESS ======================
# class ClientGoalResponse(BaseModel):
#     id: UUID
#     title: str
#     description: Optional[str] = None
#     target_date: Optional[datetime] = None
#     status: str
#     created_at: datetime

#     model_config = ConfigDict(from_attributes=True)


# class ClientGoalCreateRequest(BaseModel):
#     title: str = Field(..., max_length=255)
#     description: Optional[str] = None
#     target_date: Optional[datetime] = None

#     model_config = ConfigDict(extra="forbid")


# class ClientProgressResponse(BaseModel):
#     id: UUID
#     goal_id: Optional[UUID] = None
#     progress_percentage: float
#     notes: Optional[str] = None
#     recorded_at: datetime

#     model_config = ConfigDict(from_attributes=True)


# # ====================== JOURNAL ======================
# class ClientJournalEntryResponse(BaseModel):
#     id: UUID
#     title: Optional[str] = None
#     content: str
#     mood_rating: Optional[int] = None
#     created_at: datetime

#     model_config = ConfigDict(from_attributes=True)


# class ClientJournalCreateRequest(BaseModel):
#     title: Optional[str] = Field(None, max_length=200)
#     content: str = Field(..., max_length=5000)
#     mood_rating: Optional[int] = Field(None, ge=1, le=10)

#     model_config = ConfigDict(extra="forbid")


# # ====================== MEDICAL & HEALTH ======================
# class ClientMedicalHistoryResponse(BaseModel):
#     conditions: Optional[list] = None
#     medications: Optional[list] = None
#     allergies: Optional[list] = None
#     notes: Optional[str] = None
#     last_updated_at: datetime

#     model_config = ConfigDict(from_attributes=True)


# class ClientMedicalHistoryUpdateRequest(BaseModel):
#     conditions: Optional[list] = None
#     medications: Optional[list] = None
#     allergies: Optional[list] = None
#     notes: Optional[str] = None

#     model_config = ConfigDict(extra="forbid")


# class ClientMedicationResponse(BaseModel):
#     id: UUID
#     medication_name: str
#     dosage: Optional[str] = None
#     frequency: Optional[str] = None
#     prescribed_by: Optional[str] = None
#     start_date: Optional[datetime] = None
#     end_date: Optional[datetime] = None

#     model_config = ConfigDict(from_attributes=True)


# class ClientAllergyResponse(BaseModel):
#     id: UUID
#     allergen: str
#     severity: Optional[str] = None
#     reaction: Optional[str] = None
#     noted_at: datetime

#     model_config = ConfigDict(from_attributes=True)


# # ====================== PREFERENCES & CONSENTS ======================
# class ClientPreferenceResponse(BaseModel):
#     notification_email: bool
#     notification_sms: bool
#     notification_push: bool
#     preferred_language: str
#     preferred_modality: Optional[str] = None
#     custom_preferences: Optional[dict] = None

#     model_config = ConfigDict(from_attributes=True)


# class ClientPreferenceUpdateRequest(BaseModel):
#     notification_email: Optional[bool] = None
#     notification_sms: Optional[bool] = None
#     notification_push: Optional[bool] = None
#     preferred_language: Optional[str] = None
#     preferred_modality: Optional[str] = None
#     custom_preferences: Optional[dict] = None

#     model_config = ConfigDict(extra="forbid")


# class ClientConsentResponse(BaseModel):
#     id: UUID
#     consent_type: str
#     version: str
#     accepted: bool
#     accepted_at: datetime
#     ip_address: Optional[str] = None

#     model_config = ConfigDict(from_attributes=True)


# # ====================== DOCUMENTS ======================
# class ClientDocumentResponse(BaseModel):
#     id: UUID
#     file_url: str
#     file_type: str
#     original_filename: str
#     uploaded_at: datetime
#     verified: bool

#     model_config = ConfigDict(from_attributes=True)


# class ClientDocumentCreateRequest(BaseModel):
#     file_url: HttpUrl
#     file_type: str = Field(..., pattern="^(pdf|image|other)$")
#     original_filename: str

#     model_config = ConfigDict(extra="forbid")


# # ====================== COMMON ======================
# class MessageResponse(BaseModel):
#     message: str