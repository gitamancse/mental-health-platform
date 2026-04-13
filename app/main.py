from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.openapi.utils import get_openapi
from starlette.middleware.base import BaseHTTPMiddleware

import logging
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.db.session import engine
from app.db.base import Base

import app.db.models  # triggers all model imports for Alembic

# ── Router Imports ─────────────────────────────────────────────────────────────
from app.modules.auth.routers.auth_router import auth_router
from app.modules.assessments.routers.assessment_router import router as assessment_router
from app.modules.users.routers.user_router import user_router
from app.modules.organizations.routers.organization_router import org_router
from app.modules.executive.routers.executive_router import executive_router
from app.modules.provider.routers.provider_router import provider_router
from app.modules.provider.routers.education_router import education_router
from app.modules.provider.routers.registration_router import router as provider_registration_router
from app.modules.provider.routers.admin_router import router as admin_provider_router
from app.modules.client.routers.client_router import client_router

Base.metadata.create_all(bind=engine)

tags_metadata = []

IS_PRODUCTION = settings.ENVIRONMENT.lower() == "production"
BASE_DIR = Path(__file__).resolve().parent
SWAGGER_HTML_PATH = BASE_DIR / "swagger_ui.html"

app = FastAPI(
    title="Mental Health Platform API",
    version="1.0.0",
    description="HIPAA-compliant teletherapy & clinic management platform",
    docs_url=None,
    redoc_url=None,
    openapi_tags=tags_metadata,
    debug=not IS_PRODUCTION,
)

OUT_FILES_DIR = BASE_DIR / "out_files"
print("STATIC PATH:", OUT_FILES_DIR)

if OUT_FILES_DIR.exists():
    app.mount(
        "/out_files",
        StaticFiles(directory=str(OUT_FILES_DIR)),
        name="out_files",
    )

if getattr(settings, "ENABLE_AUTH_ROUTERS", True):
    tags_metadata.append({
        "name": "Authentication",
        "description": "Login, register, password reset, email verification"
    })

if getattr(settings, "ENABLE_USER_ROUTERS", True):
    tags_metadata.extend([
        {"name": "Users", "description": "User profile, status, basic operations"},
        {"name": "Users|Admin", "description": "Admin-only user management"},
    ])

if getattr(settings, "ENABLE_ORGANIZATIONS_ROUTERS", True):
    tags_metadata.append({
        "name": "Organizations",
        "description": "Clinic / Group practice management"
    })

if getattr(settings, "ENABLE_EXECUTIVE_ROUTERS", True):
    tags_metadata.append({
        "name": "Executive",
        "description": "Executive & clinic staff profiles"
    })

if getattr(settings, "ENABLE_PROVIDER_ROUTERS", True):
    tags_metadata.extend([
        {"name": "Provider", "description": "Provider self-profile & visibility"},
        {"name": "Provider|Licenses", "description": "State licenses & verification"},
        {"name": "Provider|Education", "description": "Degrees, certifications, CME"},
        {"name": "Provider|Subscription", "description": "Provider billing & premium features"},
        {"name": "Provider Onboarding", "description": "Provider registration, NPI verification"},
        {"name": "Admin - Provider Management", "description": "Admin approvals, rejections, audit logs"},
    ])

if getattr(settings, "ENABLE_CLIENT_ROUTERS", True):
    tags_metadata.append({
        "name": "Client",
        "description": "Client profiles, intake forms, therapy sessions"
    })


class ErrorNotificationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            path = str(request.url.path)
            method = request.method

            body = None
            try:
                body_bytes = await request.body()
                body = body_bytes.decode("utf-8", errors="replace")[:4000]
            except Exception:
                body = "<could not read body>"

            log_extra = {
                "path": path,
                "method": method,
                "request_body": body,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
            }
            logging.exception("Unhandled exception occurred", extra=log_extra, exc_info=True)

            if not IS_PRODUCTION:
                raise exc

            return JSONResponse(
                content={"detail": "Internal server error"},
                status_code=500,
            )

app.add_middleware(ErrorNotificationMiddleware)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.JWT_SECRET_KEY,
    max_age=60 * 60 * 24 * 30,
    same_site="lax",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if getattr(settings, "ENABLE_AUTH_ROUTERS", True):
    app.include_router(auth_router, prefix="/api", tags=["Authentication"])

app.include_router(assessment_router)

if getattr(settings, "ENABLE_USER_ROUTERS", True):
    app.include_router(user_router, prefix="/api", tags=["Users"])

if getattr(settings, "ENABLE_ORGANIZATIONS_ROUTERS", True):
    app.include_router(org_router, prefix="/api/organizations", tags=["Organizations"])

if getattr(settings, "ENABLE_EXECUTIVE_ROUTERS", True):
    app.include_router(executive_router, prefix="/api/executive", tags=["Executive"])

if getattr(settings, "ENABLE_PROVIDER_ROUTERS", True):
    app.include_router(provider_router, prefix="/api/provider", tags=["Provider|Provider"])
    app.include_router(
        education_router,
        prefix="/api/provider/education",
        tags=["Provider|Education"]
    )
    app.include_router(provider_registration_router, prefix="/api", tags=["Provider Onboarding"])
    app.include_router(admin_provider_router, prefix="/api", tags=["Admin - Provider Management"])

if getattr(settings, "ENABLE_CLIENT_ROUTERS", True):
    app.include_router(client_router, prefix="/api/client", tags=["Client"])

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    if not SWAGGER_HTML_PATH.exists():
        return HTMLResponse(
            content="<h1>swagger_ui.html not found</h1>",
            status_code=500
        )

    html = SWAGGER_HTML_PATH.read_text(encoding="utf-8")
    html = html.replace("{{APP_TITLE}}", app.title)
    html = html.replace("{{OPENAPI_URL}}", app.openapi_url)
    return HTMLResponse(content=html)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version="3.0.2",
        description=app.description,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/", summary="Welcome Endpoint")
def root():
    return {
        "message": "Mental Health Platform API is running",
        "status": "healthy",
        "version": "1.0.0",
    }

@app.get("/health", summary="Health Check")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }
