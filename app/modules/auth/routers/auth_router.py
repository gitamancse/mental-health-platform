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
    VerifyEmailResponse,
)
from app.modules.auth.services.auth_service import (
    register_client,
    register_provider,
    register_admin,
    authenticate_user,
    create_access_token,
    verify_email_code,
    create_password_reset_token,
    reset_user_password,
    blacklist_token,
)
from app.modules.users.models.user_model import User, UserRole

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register/client", response_model=Token)
async def register_client_endpoint(
    payload: RegisterClientRequest,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    user = register_client(db, payload, background_tasks)
    token, _ = create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


# @auth_router.post("/register/provider", response_model=Token)
# async def register_provider_endpoint(
#     payload: RegisterProviderRequest,
#     db: Session = Depends(get_db),
#     background_tasks: BackgroundTasks = None,
# ):
#     user = register_provider(db, payload, background_tasks)
#     token, _ = create_access_token(user)
#     return {"access_token": token, "token_type": "bearer"}


@auth_router.post("/admin/register/admin", response_model=MessageResponse)
async def register_admin_endpoint(
    payload: RegisterAdminRequest,
    current_super_admin: User = Depends(get_current_super_admin),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None,
):
    register_admin(db, payload, background_tasks)
    return {"message": "Admin user created successfully"}


@auth_router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request: Request = None,
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.is_verified and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Please verify your email first")

    token, _ = create_access_token(user)
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
        blacklist_token(db, token, str(current_user.id))
    return {"message": "Successfully logged out"}


@auth_router.get("/me", response_model=UserMeResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


@auth_router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    verify_email_code(db, payload.email, payload.code)
    return {"message": "Email verified successfully"}


@auth_router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    create_password_reset_token(db, payload.email, background_tasks)
    return {"message": "If an account exists, a reset link has been sent."}


@auth_router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_user_password(db, payload.token, payload.new_password)
    return {"message": "Password reset successfully"}