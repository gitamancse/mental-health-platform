# Import all models here (for Alembic / metadata)
from app.db.base import Base
from app.modules.users.models.user_model import (
    User,
    AdminProfile,
    ProviderProfile,
    ClientProfile,
    ProviderLicense,
    ProviderDocument,
    AuditLog,
)

from app.modules.auth.models.auth_model import BlacklistedToken 
from app.modules.users.models.user_model import User, ProviderProfile, AdminProfile, ClientProfile
from app.modules.provider.models.provider_registration import ProviderRegistration
