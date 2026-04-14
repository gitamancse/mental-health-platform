# app/db/models.py
"""
Central model registry for Alembic migrations + SQLAlchemy metadata.
Import EVERY model here so `alembic revision --autogenerate` sees all tables.
"""

# ── Core & Auth ─────────────────────────────────────────────────────────────
from app.modules.auth.models.auth_model import BlacklistedToken

from app.modules.users.models.user_model import (
    User,
    AdminProfile,
    
    ClientProfile,
    AuditLog,
    AdminActivityLog,
    
)

<<<<<<< Updated upstream
# ── Organizations (Multi-tenancy) ───────────────────────────────────────────
from app.modules.organizations.models.organization_model import (
    Organization,
    OrganizationMember,
    OrganizationInvite,
    OrganizationBillingInfo,
    OrganizationBranding,
    OrganizationSetting,

)

# ── Executive Module ────────────────────────────────────────────────────────
from app.modules.executive.models.executive_model import (         
    ExecutivePermission,
    ExecutiveActivityLog,
    ClinicStaff,
    ClinicAnnouncement,
)

# ── Provider Module (all 4 models) ──────────────────────────────────────────
from app.modules.provider.models.provider_model import ProviderAvailability, ProviderBlockedTime, ProviderReview, ProviderSubscription, ProviderPublicationRequest, ProviderGallery, ProviderWaitlist, ProviderDocument, ProviderLicense
from app.modules.provider.models.education_model import ProviderEducation
=======

# ── Provider Module ─────────────────────────────────────────────────────────
from app.modules.provider.models.provider_model import (
    ProviderAvailability,
    ProviderProfile,
    ProviderBlockedTime,
    ProviderReview,
    ProviderSubscription,
    ProviderPublicationRequest,
    ProviderGallery,
    ProviderWaitlist,
    ProviderDocument,
    ProviderLicense,
)

from app.modules.provider.models.provider_registration import ProviderRegistration
>>>>>>> Stashed changes

# ── Client Module (add when you create it) ──────────────────────────────────
from app.modules.client.models.client_model import ClientProfile, ClientSubscription, ClientIntakeForm, ClientAssessment, ClientConsent, ClientPreference, ClientMedicalHistory, ClientTherapySession, ClientNote, ClientGoal, ClientProgress, ClientJournalEntry, ClientAppointment, ClientMedication, ClientAllergy, ClientDocument


# This ensures Base.metadata includes everything
__all__ = [
<<<<<<< Updated upstream
    "User", "AdminProfile", "AuditLog", "AdminActivityLog", "ExecutiveProfile",
    "Organization", "OrganizationMember", "OrganizationInvite",
    "OrganizationSettings", "OrganizationBillingInfo", "OrganizationSubscription", "OrganizationBranding",
    "ProviderProfile", "ProviderLicense", "ProviderEducation", "ProviderSubscription",
=======
    "User", "AdminProfile",  "ProviderProfile", "ClientProfile",
    "AuditLog", "AdminActivityLog","ProviderDocument",
    "ProviderLicense",
    
    "ProviderAvailability", "ProviderBlockedTime", "ProviderReview", "ProviderSubscription",
    "ProviderPublicationRequest", "ProviderGallery", "ProviderWaitlist", "ProviderEducation", "ProviderRegistration",
    "ClientSubscription", "ClientIntakeForm", "ClientAssessment", "ClientConsent",
    "ClientPreference", "ClientMedicalHistory", "ClientTherapySession", "ClientNote",
    "ClientGoal", "ClientProgress", "ClientJournalEntry", "ClientAppointment",
    "ClientMedication", "ClientAllergy", "ClientDocument",
>>>>>>> Stashed changes
    "BlacklistedToken",
    # Add more as you create modules
]