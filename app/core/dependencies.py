# app/core/dependencies.py
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.modules.users.models.user_model import User
from app.modules.auth.services.auth_service import is_token_blacklisted


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        jti = payload.get("jti")
        if email is None or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    if is_token_blacklisted(db, jti):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise credentials_exception

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def get_current_super_admin(current_user: User = Depends(get_current_admin)) -> User:
    """Only super admin can create other admins"""
    if not current_user.admin_profile or not current_user.admin_profile.is_super_admin:
        raise HTTPException(
            status_code=403,
            detail="Super admin privileges required"
        )
    return current_user


def get_current_provider(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "provider":
        raise HTTPException(status_code=403, detail="Provider access required")
    return current_user


def get_current_client(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "client":
        raise HTTPException(status_code=403, detail="Client access required")
    return current_user


async def get_optional_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User | None:
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None
from fastapi import Depends, HTTPException, status
from app.modules.users.models.user_model import User, UserRole
# Import your existing get_current_user dependency

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Security dependency to ensure the logged-in user has Admin privileges.
    Used to protect sensitive healthcare administrative routes.
    """
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=
            "Access denied. Administrative privileges required."
        )
    
    if not current_user.is_active or current_user.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is inactive or disabled."
        )
        
    return current_user