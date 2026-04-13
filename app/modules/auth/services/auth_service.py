from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets
from passlib.context import CryptContext

from app.core.config import settings
from app.modules.users.models.user_model import User, UserRole, AccountStatus, AdminProfile, ProviderProfile
from app.modules.client.models.client_model import ClientProfile
from app.modules.auth.models.auth_model import BlacklistedToken
from app.modules.auth.schemas.auth_schema import (
    RegisterClientRequest,
    RegisterProviderRequest,
    RegisterAdminRequest,
)
from app.utils.email import send_email


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user: User) -> tuple[str, str]:
    jti = secrets.token_hex(16)
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user.email,
        "user_id": str(user.id),
        "role": user.role.value,
        "jti": jti,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def blacklist_token(db: Session, token: str, user_id: str) -> None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        expires_at = datetime.fromtimestamp(payload.get("exp"))
        db.add(BlacklistedToken(jti=jti, user_id=user_id, expires_at=expires_at))
        db.commit()
    except Exception:
        pass

def is_token_blacklisted(db: Session, jti: str) -> bool:
    """Check if token has been revoked"""
    token = db.query(BlacklistedToken).filter(
        BlacklistedToken.jti == jti,
        BlacklistedToken.expires_at > datetime.utcnow()
    ).first()
    return token is not None

def authenticate_user(db: Session, email: str, password: str) -> User | None:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is suspended")
    return user


# ====================== REGISTRATION ======================
def register_client(db: Session, payload: RegisterClientRequest, background_tasks: BackgroundTasks) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        role=UserRole.CLIENT,
        account_status=AccountStatus.ACTIVE,
        is_verified=False,
        is_active=True,
        email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(ClientProfile(user_id=user.id))
    db.commit()

    background_tasks.add_task(send_verification_email, db, user)
    return user


def register_provider(db: Session, payload: RegisterProviderRequest, background_tasks: BackgroundTasks) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        phone_number=payload.phone_number,
        role=UserRole.PROVIDER,
        account_status=AccountStatus.PENDING,
        is_verified=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = ProviderProfile(
        user_id=user.id,
        professional_title=payload.professional_title,
        years_of_experience=payload.years_of_experience,
        bio=payload.bio,
        specialties=payload.specialties,
        languages=payload.languages,
        accepting_new_clients=True,
        is_published=False,
    )
    db.add(profile)

    for lic in payload.licenses:
        db.add(ProviderLicense(
            user_id=user.id,
            license_number=lic.license_number,
            state=lic.state,
            expiry_date=lic.expiry_date,
            is_verified=False,
        ))

    db.commit()

    background_tasks.add_task(send_verification_email, db, user)
    return user


def register_admin(db: Session, payload: RegisterAdminRequest, background_tasks: BackgroundTasks):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name,
        role=UserRole.ADMIN,
        account_status=AccountStatus.ACTIVE,
        is_verified=True,
        is_active=True,
        email_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    db.add(AdminProfile(
        user_id=user.id,
        admin_title=payload.admin_title,
        department=payload.department,
        is_super_admin=False,
        permissions=payload.permissions or ["user_management", "provider_approval"],
    ))
    db.commit()


# ====================== EMAIL VERIFICATION ======================
def send_verification_email(db: Session, user: User):
    code = secrets.token_hex(4).upper()
    expiry = datetime.utcnow() + timedelta(minutes=20)

    user.verification_code = code
    user.verification_code_expiry = expiry
    db.commit()

    subject = "Verify your email - Mental Health Platform"
    body = f"""
    Hi {user.full_name},

    Thank you for registering!

    Your verification code is: {code}

    This code expires in 20 minutes.
    """

    try:
        send_email(to_email=user.email, subject=subject, body=body)
    except Exception as e:
        print(f"Failed to send verification email: {e}")


def verify_email_code(db: Session, email: str, code: str) -> None:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.verification_code or not user.verification_code_expiry:
        raise HTTPException(status_code=400, detail="No verification code found")

    if user.verification_code_expiry < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Verification code has expired")

    if user.verification_code != code:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    user.is_verified = True
    user.email_verified = True
    user.verification_code = None
    user.verification_code_expiry = None
    db.commit()


# ====================== PASSWORD RESET ======================
def create_password_reset_token(db: Session, email: str, background_tasks: BackgroundTasks):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return

    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(minutes=30)

    user.password_reset_token = token
    user.password_reset_expiry = expiry
    db.commit()

    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    subject = "Reset your password - Mental Health Platform"
    body = f"""
    Hi {user.full_name},

    You requested a password reset.

    Click here to reset your password: {reset_link}

    This link expires in 30 minutes.
    """

    background_tasks.add_task(send_email, user.email, subject, body)


def reset_user_password(db: Session, token: str, new_password: str) -> None:
    user = db.query(User).filter(
        User.password_reset_token == token,
        User.password_reset_expiry > datetime.utcnow()
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired reset token")

    user.hashed_password = get_password_hash(new_password)
    user.password_reset_token = None
    user.password_reset_expiry = None
    user.password_changed_at = datetime.utcnow()
    db.commit()