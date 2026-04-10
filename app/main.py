from fastapi import FastAPI
from app.modules.auth.routers.auth_router import auth_router
# 1. Import the new routers
from app.modules.provider.routers.registration_router import router as provider_registration_router
from app.modules.provider.routers.admin_router import router as admin_provider_router

app = FastAPI(
    title="BTT Mental Health Platform API",
    description="HIPAA-compliant backend for provider and client management",
    version="1.0.0"
)

# 2. Include routers with consistent versioned prefixes
# Authentication (Login, MFA, Password Reset)
app.include_router(auth_router, prefix="/api", tags=["Authentication"])

# Provider Public/Onboarding (Registration, NPI Verification)
app.include_router(provider_registration_router, prefix="/api", tags=["Provider Onboarding"])

# Admin Management (Approvals, Rejections, Audit Logs)
app.include_router(admin_provider_router, prefix="/api", tags=["Admin - Provider Management"])

@app.get("/", tags=["Health Check"])
def root():
    """
    Basic health check endpoint.
    """
    return {
        "status": "online",
        "message": "BTT API is running",
        "version": "1.0.0"
    }