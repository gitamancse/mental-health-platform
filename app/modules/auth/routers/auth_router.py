# app\modules\auth\routers\auth_router.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_super_admin, get_db, get_current_user
from app.modules.auth.schemas.auth_schema import (
    RegisterClientRequest,
    RegisterProviderRequest,
    RegisterAdminRequest,
    Token,
    UserMeResponse,
    MessageResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    VerifyEmailResponse
)
from app.modules.auth.services.auth_service import (
    
    AuthService
)
from app.modules.users.models.user_model import User, UserRole

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register/client", response_model=Token)
async def register_client_endpoint(
    payload: RegisterClientRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    user = AuthService.register_client(db, payload, background_tasks)
    token, _ = AuthService.create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}

@auth_router.post("/admin/register/admin", response_model=MessageResponse)
async def register_admin_endpoint(
    payload: RegisterAdminRequest,
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    AuthService.register_admin(db, payload, background_tasks)
    return {"message": "Admin user created successfully"}


@auth_router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_verified and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    token, _ = AuthService.create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/logout", response_model=MessageResponse)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    request: Request = None,
):
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        AuthService.blacklist_token(db, token, str(current_user.id))
    return {"message": "Successfully logged out"}


@auth_router.get("/me", response_model=UserMeResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@auth_router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    AuthService.verify_email_code(db, payload.email, payload.code)
    return {"message": "Email verified successfully"}


@auth_router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    AuthService.create_password_reset_token(db, payload.email, background_tasks)
    return {"message": "If an account exists, a reset link has been sent."}


@auth_router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    AuthService.reset_user_password(db, payload.token, payload.new_password)
    return {"message": "Password reset successfully"}
@auth_router.post("/password-reset/request")
async def request_reset(email: str, db: Session = Depends(get_db)):
    return await AuthService.request_password_reset(db, email)

@auth_router.post("/password-reset/confirm")
async def confirm_reset(token: str, new_password: str, db: Session = Depends(get_db)):
    return await AuthService.reset_password(db, token, new_password)

@auth_router.get("/mfa/setup")
async def setup_mfa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    secret, uri = AuthService.generate_mfa_secret(current_user)
    # Save secret to user (but don't enable MFA yet)
    current_user.verification_code = secret # Reusing column or add 'mfa_secret'
    db.commit()
    return {"qr_code_uri": uri, "secret": secret}

@auth_router.post("/mfa/enable")
async def enable_mfa(code: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if AuthService.verify_mfa_code(current_user.verification_code, code):
        current_user.mfa_enabled = True
        db.commit()
        return {"message": "MFA enabled successfully"}
    raise HTTPException(status_code=400, detail="Invalid MFA code")
