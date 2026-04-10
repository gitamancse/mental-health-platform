import sys
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

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
from app.modules.provider.models.provider_registration import ProviderRegistration
from app.modules.provider.models.admin_action import AdminAction
from app.modules.auth.services.auth_service import get_password_hash

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def create_enum_types():
    """Create enum types if they don't exist"""
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        # Check if enum types exist, create if they don't
        enum_types = [
            {
                "name": "userrole",
                "values": ["super_admin", "admin", "provider", "client"]
            },
            {
                "name": "accountstatus",
                "values": ["pending", "active", "suspended", "deleted"]
            },
            {
                "name": "registrationstatus",
                "values": [
                    "pending_npi_validation",
                    "pending_admin_review",
                    "approved",
                    "rejected",
                    "request_revisions"
                ]
            },
            {
                "name": "actiontype",
                "values": [
                    "approve_registration",
                    "reject_registration",
                    "manual_npi_override",
                    "publish_profile",
                    "request_revisions"
                ]
            }
        ]

        for enum_type in enum_types:
            # Check if enum type exists
            result = conn.execute(
                text("SELECT 1 FROM pg_type WHERE typname = :enum_name"),
                {"enum_name": enum_type["name"]}
            ).fetchone()

            if not result:
                # Create the enum type
                values = ", ".join([f"'{v}'" for v in enum_type["values"]])
                conn.execute(
                    text(f"CREATE TYPE {enum_type['name']} AS ENUM ({values})")
                )
                print(f"Created enum type: {enum_type['name']}")
            else:
                # Check for missing values and add them
                existing = conn.execute(
                    text(
                        """
                        SELECT e.enumlabel
                        FROM pg_type t
                        JOIN pg_enum e ON t.oid = e.enumtypid
                        WHERE t.typname = :enum_name
                        ORDER BY e.enumsortorder
                        """
                    ),
                    {"enum_name": enum_type["name"]},
                ).fetchall()

                existing_values = {row[0] for row in existing}

                for value in enum_type["values"]:
                    if value not in existing_values:
                        print(f"Adding missing enum value '{value}' to '{enum_type['name']}'...")
                        conn.execute(text(f"ALTER TYPE {enum_type['name']} ADD VALUE '{value}'"))

def create_user_if_not_exists(db: Session, email: str, user_data: dict, profile_data: dict, profile_type: str):
    """Helper function to create a user and their profile if they don't exist"""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        print(f"Creating {profile_type} with email {email}...")
        user = User(
            email=email,
            hashed_password=get_password_hash(user_data.get("password", "Password@123")),
            full_name=user_data["full_name"],
            role=user_data["role"],
            account_status=user_data.get("account_status", AccountStatus.PENDING),
            is_verified=user_data.get("is_verified", False),
            email_verified=user_data.get("email_verified", True),
            is_active=user_data.get("is_active", True),
        )
        db.add(user)
        db.flush()

        # Create the appropriate profile
        if profile_type == "admin":
            profile = AdminProfile(
                user_id=user.id,
                admin_title=profile_data.get("admin_title", "Administrator"),
                department=profile_data.get("department", "Operations"),
                is_super_admin=profile_data.get("is_super_admin", False),
                permissions=profile_data.get("permissions", []),
            )
        elif profile_type == "provider":
            # Only include fields that actually exist in ProviderProfile
            profile = ProviderProfile(
                user_id=user.id,
                professional_title=profile_data.get("professional_title", "Therapist"),
                years_of_experience=profile_data.get("years_of_experience", 0),
                bio=profile_data.get("bio", ""),
                specialties=profile_data.get("specialties", []),
                modalities=profile_data.get("modalities", []),
                languages=profile_data.get("languages", []),
                insurance_accepted=profile_data.get("insurance_accepted", []),
                accepting_new_clients=profile_data.get("accepting_new_clients", True),
                is_published=profile_data.get("is_published", False),
                average_rating=profile_data.get("average_rating", 0.0),
                total_reviews=profile_data.get("total_reviews", 0),
                #status=profile_data.get("status", "draft"),
                #published_at=profile_data.get("published_at"),
                profile_status=profile_data.get("status", "draft"), 
                published_at=profile_data.get("published_at"),
            )
        elif profile_type == "client":
            profile = ClientProfile(
                user_id=user.id,
                preferred_language=profile_data.get("preferred_language", "English"),
                total_sessions=profile_data.get("total_sessions", 0),
                self_assessment_data=profile_data.get("self_assessment_data", {}),
                preferences=profile_data.get("preferences", {}),
            )

        db.add(profile)

        # Create license if this is a provider
        if profile_type == "provider" and profile_data.get("license_number"):
            license = ProviderLicense(
                user_id=user.id,
                license_number=profile_data["license_number"],
                state=profile_data.get("license_state", "CA"),
                expiry_date=profile_data.get("expiry_date", utc_now() + timedelta(days=365)),
                is_verified=profile_data.get("is_verified", True),
                verified_at=profile_data.get("verified_at", utc_now()),
                verified_by=profile_data.get("verified_by"),
            )
            db.add(license)

        db.flush()
        print(f"✅ {profile_type.capitalize()} created with ID: {user.id}")
        return user
    else:
        print(f"✔ {profile_type.capitalize()} with email {email} already exists (ID: {user.id})")
        return user

def create_provider_registration_if_not_exists(db: Session, email: str, registration_data: dict):
    """Helper function to create a provider registration if it doesn't exist"""
    registration = db.query(ProviderRegistration).filter(ProviderRegistration.email == email).first()
    if not registration:
        print(f"Creating provider registration for {email}...")

        # First create the user if they don't exist
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                hashed_password=get_password_hash(registration_data.get("password", "Provider@123")),
                full_name=registration_data["full_name"],
                role=UserRole.PROVIDER,
                account_status=registration_data.get("account_status", AccountStatus.PENDING),
                is_verified=registration_data.get("is_verified", False),
                email_verified=registration_data.get("email_verified", True),
                is_active=registration_data.get("is_active", True),
            )
            db.add(user)
            db.flush()

        registration = ProviderRegistration(
            user_id=user.id,
            title=registration_data.get("title", "Dr"),
            first_name=registration_data["first_name"],
            middle_name=registration_data.get("middle_name"),
            last_name=registration_data["last_name"],
            email=email,
            address_line1="123 Main St",
            city="San Francisco",
            postcode="94105",
            country="US",
            licensing_board="California Board of Psychology",
            registry_id="REG123456",
            membership_type="Accredited Member",
            professional_role=registration_data["professional_role"],
            academic_degree=registration_data.get("academic_degree"),
            npi_number=registration_data["npi_number"],
            npi_validated=registration_data.get("npi_validated", False),
            license_number=registration_data["license_number"],
            license_state=registration_data.get("license_state", "CA"),
            license_proof_url=registration_data.get("license_proof_url"),
            status=registration_data["status"],
            admin_notes=registration_data.get("admin_notes"),
            rejection_reason=registration_data.get("rejection_reason"),
            submitted_at=registration_data.get("submitted_at", utc_now()),
        )

        if registration_data.get("reviewed_by"):
            registration.reviewed_by = registration_data["reviewed_by"]
            registration.reviewed_at = registration_data.get("reviewed_at", utc_now())

        db.add(registration)
        db.flush()
        print(f"✅ Provider registration created with ID: {registration.id}")
        return registration
    else:
        print(f"✔ Provider registration for {email} already exists (ID: {registration.id})")
        return registration

def create_admin_action_if_not_exists(db: Session, action_data: dict):
    """Helper function to create an admin action if it doesn't exist"""
    # Check if an action with the same target_id and action_type already exists
    existing_action = db.query(AdminAction).filter(
        AdminAction.target_id == action_data["target_id"],
        AdminAction.action_type == action_data["action_type"]
    ).first()

    if not existing_action:
        print(f"Creating admin action {action_data['action_type']} for target {action_data['target_id']}...")

        action = AdminAction(
            admin_id=action_data["admin_id"],
            user_id=action_data.get("user_id"),
            action_type=action_data["action_type"],
            target_id=action_data["target_id"],
            target_type=action_data["target_type"],
            action_metadata=action_data.get("action_metadata", {}),
            created_at=action_data.get("created_at", utc_now())
        )

        db.add(action)
        db.flush()
        print(f"✅ Admin action created with ID: {action.id}")
        return action
    else:
        print(f"✔ Admin action {action_data['action_type']} for target {action_data['target_id']} already exists (ID: {existing_action.id})")
        return existing_action

def load_dummy_data():
    print("\n=== Starting Dummy Data Loader ===\n")

    # First create enum types if they don't exist
    print("Ensuring enum types exist...")
    create_enum_types()

    db: Session = SessionLocal()

    try:
        # Get or create admin user first (needed for other operations)
        admin_user = create_user_if_not_exists(
            db=db,
            email="admin@btt.com",
            user_data={
                "full_name": "System Admin",
                "role": UserRole.ADMIN,
                "account_status": AccountStatus.ACTIVE,
                "is_verified": True,
                "password": "Admin@123456"
            },
            profile_data={
                "admin_title": "Operations Admin",
                "department": "Operations",
                "permissions": ["user_management", "provider_approval"]
            },
            profile_type="admin"
        )

        # Get or create super admin
        super_admin = create_user_if_not_exists(
            db=db,
            email="superadmin@btt.com",
            user_data={
                "full_name": "Super Admin",
                "role": UserRole.SUPER_ADMIN,
                "account_status": AccountStatus.ACTIVE,
                "is_verified": True,
                "password": "SuperAdmin@123"
            },
            profile_data={
                "admin_title": "Chief Admin",
                "department": "Management",
                "is_super_admin": True,
                "permissions": ["all_access"]
            },
            profile_type="admin"
        )

        # ================= CREATE PROVIDER REGISTRATION =================
        provider_registration = create_provider_registration_if_not_exists(
            db=db,
            email="newprovider@btt.com",
            registration_data={
                "full_name": "Dr. Sarah Johnson",
                "first_name": "Sarah",
                "middle_name": "Marie",
                "last_name": "Johnson",
                "professional_role": "Licensed Clinical Psychologist",
                "academic_degree": "PhD",
                "npi_number": "1234567890",
                "npi_validated": True,
                "license_number": "LIC987654",
                "license_state": "CA",
                "license_proof_url": "https://storage.example.com/licenses/LIC987654.pdf",
                "status": "pending_admin_review",
                "password": "Provider@123"
            }
        )

        # Create approval action for the registration if it doesn't exist
        if provider_registration:
            create_admin_action_if_not_exists(
                db=db,
                action_data={
                    "admin_id": admin_user.id,
                    "user_id": provider_registration.user_id,
                    "action_type": "approve_registration",
                    "target_id": provider_registration.id,
                    "target_type": "provider_registration",
                    "action_metadata": {
                        "previous_status": "pending_admin_review",
                        "new_status": "approved",
                        "notes": "Initial registration created"
                    },
                    "created_at": utc_now()
                }
            )

        # ================= CREATE APPROVED PROVIDER =================
        approved_provider = create_user_if_not_exists(
            db=db,
            email="provider@btt.com",
            user_data={
                "full_name": "Dr. John Doe",
                "role": UserRole.PROVIDER,
                "account_status": AccountStatus.ACTIVE,
                "is_verified": True,
                "password": "Provider@123"
            },
            profile_data={
                "professional_title": "Clinical Psychologist",
                "years_of_experience": 8,
                "bio": "Experienced mental health professional specializing in anxiety and depression",
                "specialties": ["anxiety", "depression", "stress management"],
                "modalities": ["CBT", "Mindfulness", "Psychodynamic"],
                "languages": ["English", "Spanish"],
                "insurance_accepted": ["Aetna", "Blue Cross", "United Healthcare"],
                "accepting_new_clients": True,
                "is_published": True,
                "average_rating": 4.5,
                "total_reviews": 20,
                "status": "published",
                "published_at": utc_now() - timedelta(days=1),
            },
            profile_type="provider"
        )

        # Create license for the approved provider
        if approved_provider:
            # Check if license already exists
            existing_license = db.query(ProviderLicense).filter(
                ProviderLicense.user_id == approved_provider.id
            ).first()

            if not existing_license:
                license = ProviderLicense(
                    user_id=approved_provider.id,
                    license_number="LIC123456",
                    state="CA",
                    expiry_date=utc_now() + timedelta(days=365),
                    is_verified=True,
                    verified_at=utc_now(),
                    verified_by=admin_user.id,
                )
                db.add(license)

            # Create approval action for the approved provider if it doesn't exist
            create_admin_action_if_not_exists(
                db=db,
                action_data={
                    "admin_id": admin_user.id,
                    "user_id": approved_provider.id,
                    "action_type": "approve_registration",
                    "target_id": approved_provider.id,
                    "target_type": "provider_profile",
                    "action_metadata": {
                        "previous_status": "pending_admin_review",
                        "new_status": "approved",
                        "notes": "Profile approved by admin"
                    },
                    "created_at": utc_now() - timedelta(days=1)
                }
            )

        # ================= CREATE REJECTED PROVIDER REGISTRATION =================
        rejected_registration = create_provider_registration_if_not_exists(
            db=db,
            email="rejectedprovider@btt.com",
            registration_data={
                "full_name": "Dr. Bad Provider",
                "first_name": "Bad",
                "last_name": "Provider",
                "professional_role": "Unlicensed Therapist",
                "npi_number": "0987654321",
                "npi_validated": False,
                "license_number": "INVALID123",
                "license_state": "CA",
                "status": "rejected",
                "rejection_reason": "Invalid license number and NPI not verified",
                "reviewed_by": admin_user.id,
                "reviewed_at": utc_now() - timedelta(days=1),
                "password": "Provider@123"
            }
        )

        # Create rejection action if it doesn't exist
        if rejected_registration:
            create_admin_action_if_not_exists(
                db=db,
                action_data={
                    "admin_id": admin_user.id,
                    "user_id": rejected_registration.user_id,
                    "action_type": "reject_registration",
                    "target_id": rejected_registration.id,
                    "target_type": "provider_registration",
                    "action_metadata": {
                        "previous_status": "pending_admin_review",
                        "new_status": "rejected",
                        "rejection_reason": "Invalid license number and NPI not verified"
                    },
                    "created_at": utc_now() - timedelta(days=1)
                }
            )

        # ================= CREATE CLIENT =================
        create_user_if_not_exists(
            db=db,
            email="client@btt.com",
            user_data={
                "full_name": "Jane Doe",
                "role": UserRole.CLIENT,
                "account_status": AccountStatus.ACTIVE,
                "is_verified": True,
                "password": "Client@123"
            },
            profile_data={
                "preferred_language": "English",
                "total_sessions": 2,
                "self_assessment_data": {
                    "anxiety_level": "moderate",
                    "depression_level": "mild",
                    "stress_level": "high"
                },
                "preferences": {
                    "therapy_type": ["cbt", "mindfulness"],
                    "gender_preference": "no_preference",
                    "session_frequency": "weekly"
                }
            },
            profile_type="client"
        )

        db.commit()
        print("\n=== Dummy Data Loaded Successfully ===\n")

    except Exception as e:
        db.rollback()
        print("❌ Error:", e)
        raise

    finally:
        db.close()

if __name__ == "__main__":
    print("Ensuring tables exist...")
    Base.metadata.create_all(bind=engine)
    load_dummy_data()