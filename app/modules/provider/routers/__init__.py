from .registration_router import router as registration_router  # NEW
from .admin_router import router as admin_router  # NEW

__all__ = [
    "registration_router",  # NEW
    "admin_router"  # NEW
]