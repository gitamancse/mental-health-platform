# app/db/models.py
"""
Central model registry for Alembic migrations + SQLAlchemy metadata.
Import EVERY model here so `alembic revision --autogenerate` sees all tables.
"""

# ── Core & Auth ─────────────────────────────────────────────────────────────
from app.modules.auth.models.auth_model import BlacklistedToken

# ── Users ───────────────────────────────────────────────────────────────────
from app.modules.users.models.user_model import (
    User,
    AdminProfile,
    ClientProfile,
    AuditLog,
    AdminActivityLog,
    
)


# ── Provider Module ─────────────────────────────────────────────────────────
from app.modules.provider.models.provider_model import (
    ProviderAvailability,
    ProviderBlockedTime,
    ProviderReview,
    ProviderSubscription,
    ProviderPublicationRequest,
    ProviderGallery,
    ProviderWaitlist,
    ProviderDocument,
    ProviderLicense,
)
from app.modules.provider.models.education_model import ProviderEducation
from app.modules.provider.models.provider_registration import ProviderRegistration

# ── Client Module ────────────────────────────────────────────────────────────
from app.modules.client.models.client_model import (
    ClientProfile,
    ClientSubscription,
    ClientIntakeForm,
    ClientAssessment,
    ClientConsent,
    ClientPreference,
    ClientMedicalHistory,
    ClientTherapySession,
    ClientNote,
    ClientGoal,
    ClientProgress,
    ClientJournalEntry,
    ClientAppointment,
    ClientMedication,
    ClientAllergy,
    ClientDocument,
)

# This ensures Base.metadata includes everything
__all__ = [
    "User", "AdminProfile",  "ProviderProfile", "ClientProfile",
    "AuditLog", "AdminActivityLog","ProviderDocument",
    "ProviderLicense",
    
    "ProviderAvailability", "ProviderBlockedTime", "ProviderReview", "ProviderSubscription",
    "ProviderPublicationRequest", "ProviderGallery", "ProviderWaitlist", "ProviderEducation", "ProviderRegistration",
    "ClientSubscription", "ClientIntakeForm", "ClientAssessment", "ClientConsent",
    "ClientPreference", "ClientMedicalHistory", "ClientTherapySession", "ClientNote",
    "ClientGoal", "ClientProgress", "ClientJournalEntry", "ClientAppointment",
    "ClientMedication", "ClientAllergy", "ClientDocument",
    "BlacklistedToken",
]
