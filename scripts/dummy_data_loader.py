import sys
import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.modules.users.models.user_model import (
    User,
    UserRole,
    AccountStatus,
    ProviderProfile,
    ClientProfile,
    AdminProfile,
    ProviderLicense,
)
from app.modules.auth.services.auth_service import get_password_hash


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_enum_values():
    """
    Ensures PostgreSQL enum labels exist before any ORM query/insert uses them.
    This is needed because your DB already has enum types created from an older version.
    """
    enum_fixes = [
        ("userrole", ["super_admin", "admin", "provider", "client"]),
        ("accountstatus", ["pending", "active", "suspended", "deleted"]),
    ]

    # Use AUTOCOMMIT because ALTER TYPE ... ADD VALUE can be problematic inside a transaction
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for enum_name, values in enum_fixes:
            existing = conn.execute(
                text(
                    """
                    SELECT e.enumlabel
                    FROM pg_type t
                    JOIN pg_enum e ON t.oid = e.enumtypid
                    JOIN pg_namespace n ON n.oid = t.typnamespace
                    WHERE t.typname = :enum_name
                    ORDER BY e.enumsortorder
                    """
                ),
                {"enum_name": enum_name},
            ).fetchall()

            existing_values = {row[0] for row in existing}

            for value in values:
                if value not in existing_values:
                    print(f"Adding missing enum value '{value}' to '{enum_name}'...")
                    conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"))


def load_dummy_data():
    print("\n=== Starting Dummy Data Loader ===\n")

    db: Session = SessionLocal()

    try:
        # Make sure enum labels exist first
        ensure_enum_values()

        # ================= CREATE SUPER ADMIN =================
        super_admin = db.query(User).filter(
            User.email == "superadmin@btt.com"
        ).first()

        if not super_admin:
            print("Creating Super Admin...")

            super_admin = User(
                email="superadmin@btt.com",
                hashed_password=get_password_hash("SuperAdmin@123"),
                full_name="Super Admin",
                role=UserRole.SUPER_ADMIN,
                account_status=AccountStatus.ACTIVE,
                is_verified=True,
                email_verified=True,
                is_active=True,
            )
            db.add(super_admin)
            db.flush()

            db.add(
                AdminProfile(
                    user_id=super_admin.id,
                    admin_title="Chief Admin",
                    department="Management",
                    is_super_admin=True,
                    permissions=["all_access"],
                )
            )
            db.flush()

            print("✅ Super Admin created")
        else:
            print("✔ Super Admin already exists")

        # ================= CREATE ADMIN =================
        admin = db.query(User).filter(
            User.email == "admin@btt.com"
        ).first()

        if not admin:
            print("Creating Admin...")

            admin = User(
                email="admin@btt.com",
                hashed_password=get_password_hash("Admin@123456"),
                full_name="System Admin",
                role=UserRole.ADMIN,
                account_status=AccountStatus.ACTIVE,
                is_verified=True,
                email_verified=True,
                is_active=True,
            )
            db.add(admin)
            db.flush()

            db.add(
                AdminProfile(
                    user_id=admin.id,
                    admin_title="Operations Admin",
                    department="Operations",
                    permissions=["user_management", "provider_approval"],
                )
            )
            db.flush()

            print("✅ Admin created")
        else:
            print("✔ Admin already exists")

        # ================= CREATE PROVIDER =================
        provider = db.query(User).filter(
            User.email == "provider@btt.com"
        ).first()

        if not provider:
            print("Creating Provider...")

            provider = User(
                email="provider@btt.com",
                hashed_password=get_password_hash("Provider@123"),
                full_name="Dr. John Doe",
                role=UserRole.PROVIDER,
                account_status=AccountStatus.ACTIVE,
                is_verified=True,
                email_verified=True,
                is_active=True,
            )
            db.add(provider)
            db.flush()

            db.add(
                ProviderProfile(
                    user_id=provider.id,
                    professional_title="Clinical Psychologist",
                    years_of_experience=8,
                    bio="Experienced mental health professional",
                    specialties=["anxiety", "depression"],
                    languages=["English", "Hindi"],
                    accepting_new_clients=True,
                    is_published=True,
                    average_rating=4.5,
                    total_reviews=20,
                )
            )

            db.add(
                ProviderLicense(
                    user_id=provider.id,
                    license_number="LIC123456",
                    state="CA",
                    expiry_date=utc_now() + timedelta(days=365),
                    is_verified=True,
                    verified_at=utc_now(),
                    verified_by=super_admin.id,
                )
            )

            db.flush()
            print("✅ Provider created")
        else:
            print("✔ Provider already exists")

        # ================= CREATE CLIENT =================
        client = db.query(User).filter(
            User.email == "client@btt.com"
        ).first()

        if not client:
            print("Creating Client...")

            client = User(
                email="client@btt.com",
                hashed_password=get_password_hash("Client@123"),
                full_name="Jane Doe",
                role=UserRole.CLIENT,
                account_status=AccountStatus.ACTIVE,
                is_verified=True,
                email_verified=True,
                is_active=True,
            )
            db.add(client)
            db.flush()

            db.add(
                ClientProfile(
                    user_id=client.id,
                    preferred_language="English",
                    total_sessions=2,
                )
            )

            db.flush()
            print("✅ Client created")
        else:
            print("✔ Client already exists")

        db.commit()
        print("\n=== Dummy Data Loaded Successfully ===\n")

    except Exception as e:
        db.rollback()
        print("❌ Error:", e)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    print("Creating tables if not exist...")
    Base.metadata.create_all(bind=engine)
    load_dummy_data()