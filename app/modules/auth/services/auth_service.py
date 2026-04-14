from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import secrets
from passlib.context import CryptContext

from app.core.config import settings
from app.core.email import EmailService # Using the robust service we built
from app.modules.users.models.user_model import User, UserRole, AccountStatus, AdminProfile
from app.modules.client.models.client_model import ClientProfile
from app.modules.auth.models.auth_model import BlacklistedToken
from app.modules.auth.schemas.auth_schema import (
    RegisterClientRequest,
    RegisterAdminRequest,
)

# Security Config
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

class AuthService:
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(user: User) -> tuple[str, str]:
        jti = secrets.token_hex(16)
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": user.email,
            "user_id": str(user.id),
            "role": user.role.value,
            "jti": jti,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return token, jti

    @staticmethod
    def is_token_blacklisted(db: Session, jti: str) -> bool:
        token = db.query(BlacklistedToken).filter(
            BlacklistedToken.jti == jti,
            BlacklistedToken.expires_at > datetime.now(timezone.utc)
        ).first()
        return token is not None

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        user = db.query(User).filter(User.email == email).first()
        if not user or not AuthService.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account is suspended")
        return user

    # ====================== REGISTRATION (CLIENT/ADMIN) ======================
    @staticmethod
    async def register_client(db: Session, payload: RegisterClientRequest):
        if db.query(User).filter(User.email == payload.email).first():
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            email=payload.email,
            hashed_password=AuthService.get_password_hash(payload.password),
            full_name=payload.full_name,
            phone_number=payload.phone_number,
            role=UserRole.CLIENT,
            account_status=AccountStatus.ACTIVE,
            is_verified=False,
            is_active=True
        )
        db.add(user)
        
        # Generate verification token
        token = secrets.token_urlsafe(32)
        user.verification_code = token
        user.verification_code_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
        
        db.flush()
        db.add(ClientProfile(user_id=user.id))
        db.commit()


        await EmailService.send_verification_email(user.email, token)
        return user

    # ====================== EMAIL VERIFICATION ======================
    @staticmethod
    def verify_email_code(db: Session, email: str, code: str) -> None:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.verification_code or user.verification_code_expiry < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Invalid or expired code")

        if user.verification_code != code:
            raise HTTPException(status_code=400, detail="Invalid verification code")

        user.is_verified = True
        user.email_verified = True
        user.verification_code = None
        user.verification_code_expiry = None
        db.commit()

    # ====================== PASSWORD RESET ======================
    @staticmethod
    async def request_password_reset(db: Session, email: str):
        user = db.query(User).filter(User.email == email).first()
        if not user:
            return # Security: don't confirm if email exists

        token = secrets.token_urlsafe(32)
        user.password_reset_token = token
        user.password_reset_expiry = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()

        await EmailService.send_password_reset_email(user.email, token)

    @staticmethod
    def reset_user_password(db: Session, token: str, new_password: str) -> None:
        user = db.query(User).filter(
            User.password_reset_token == token,
            User.password_reset_expiry > datetime.now(timezone.utc)
        ).first()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid or expired reset token")

        user.hashed_password = AuthService.get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expiry = None
        user.password_changed_at = datetime.now(timezone.utc)
        db.commit()
