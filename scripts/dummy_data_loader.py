import sys
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, engine
from app.db.base import Base

# ====================== ALL MODEL IMPORTS ======================
from app.modules.users.models.user_model import (
    User, UserRole, AccountStatus,
    AdminProfile, ExecutiveProfile, ProviderProfile, ClientProfile,
    AuditLog, AdminActivityLog,
)
from app.modules.auth.models.auth_model import (
    BlacklistedToken, UserMFABackupCode, LoginAttempt,
    PasswordHistory, SystemSetting,
)
from app.modules.organizations.models.organization_model import (
    Organization, OrganizationMember, OrganizationSetting,
    OrganizationBillingInfo, OrganizationInvite, OrganizationBranding,
    OrgStatus,
)
from app.modules.executive.models.executive_model import (
    ExecutivePermission, ExecutiveActivityLog,
    ClinicStaff, ClinicAnnouncement,
)
from app.modules.provider.models.education_model import ProviderEducation
from app.modules.provider.models.provider_model import (
    ProviderAvailability, ProviderBlockedTime, ProviderReview,
    ProviderSubscription, ProviderPublicationRequest,
    ProviderGallery, ProviderWaitlist, ProviderLicense, ProviderDocument,
)
from app.modules.client.models.client_model import (
    ClientSubscription, ClientIntakeForm, ClientAssessment,
    ClientConsent, ClientPreference, ClientMedicalHistory,
    ClientTherapySession, ClientNote, ClientGoal, ClientProgress,
    ClientJournalEntry, ClientAppointment, ClientMedication,
    ClientAllergy, ClientDocument,
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
def reset_database_completely():
    """Forcefully reset the entire public schema — best for dev dummy data"""
    print("🔥 Performing complete database reset (DROP SCHEMA CASCADE)...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()
    print("✅ Database fully reset and ready for fresh schema creation.\n")


def ensure_enum_values():
    """Add any missing enum values to PostgreSQL types"""
    enum_fixes = [
        ("userrole", ["super_admin", "admin", "executive", "provider", "client"]),
        ("accountstatus", ["pending", "active", "suspended", "deleted"]),
        ("orgstatus", ["pending", "active", "suspended"]),
    ]
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for enum_name, values in enum_fixes:
            existing = conn.execute(text(
                """
                SELECT e.enumlabel FROM pg_type t
                JOIN pg_enum e ON t.oid = e.enumtypid
                JOIN pg_namespace n ON n.oid = t.typnamespace
                WHERE t.typname = :enum_name
                """
            ), {"enum_name": enum_name}).fetchall()
            existing_values = {row[0] for row in existing}
            for value in values:
                if value not in existing_values:
                    print(f"Adding missing enum value '{value}' to '{enum_name}'...")
                    conn.execute(text(f"ALTER TYPE {enum_name} ADD VALUE IF NOT EXISTS '{value}'"))


def load_dummy_data():
    print("\n=== Starting Comprehensive Dummy Data Loader ===\n")
    db: Session = SessionLocal()

    try:
        ensure_enum_values()

        # ===================================================================
        # 1. CORE USERS + PROFILES
        # ===================================================================
        # SUPER ADMIN
        super_admin = db.query(User).filter(User.email == "superadmin@btt.com").first()
        if not super_admin:
            super_admin = User(
                email="superadmin@btt.com",
                hashed_password=get_password_hash("SuperAdmin@123"),
                full_name="Dr. Michael Rivera",
                phone_number="+1-555-0101",
                role=UserRole.SUPER_ADMIN,
                account_status=AccountStatus.ACTIVE,
                is_verified=True,
                email_verified=True,
                is_active=True,
                mfa_enabled=True,
            )
            db.add(super_admin)
            db.flush()
            db.add(
                AdminProfile(
                    user_id=super_admin.id,
                    admin_title="Platform Superintendent",
                    department="Executive Leadership",
                    is_super_admin=True,
                    permissions=["all_access", "system_config", "billing_master"],
                    notes="Founding super admin",
                    profile_picture_url="https://btt.com/uploads/avatars/superadmin.jpg",
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
            db.flush()
            print("✅ Super Admin + AdminProfile created")

        # ADMIN
        admin = db.query(User).filter(User.email == "admin@btt.com").first()
        if not admin:
            admin = User(
                email="admin@btt.com",
                hashed_password=get_password_hash("Admin@123456"),
                full_name="Priya Sharma",
                phone_number="+1-555-0102",
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
                    admin_title="Operations Director",
                    department="Compliance & Onboarding",
                    is_super_admin=False,
                    permissions=["user_management", "provider_approval", "audit_view"],
                    profile_picture_url="https://btt.com/uploads/avatars/admin.jpg",
                )
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
            print("✅ Admin + AdminProfile created")

        # EXECUTIVE
        executive = db.query(User).filter(User.email == "executive@btt.com").first()
        if not executive:
            executive = User(
                email="executive@btt.com",
                hashed_password=get_password_hash("Executive@123"),
                full_name="Sarah Chen",
                phone_number="+1-555-0103",
                role=UserRole.EXECUTIVE,
                account_status=AccountStatus.ACTIVE,
                is_verified=True,
                email_verified=True,
                is_active=True,
            )
            db.add(executive)
            db.flush()
            exec_profile = ExecutiveProfile(
                user_id=executive.id,
                executive_title="Clinical Director",
                department="Behavioral Health",
                organization_name="BTT Mental Health Group",
                permissions=["provider_onboarding", "billing_view", "analytics"],
                profile_picture_url="https://btt.com/uploads/avatars/executive.jpg",
            )
            db.add(exec_profile)
            db.flush()
            print("✅ Executive + ExecutiveProfile created")

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
        # PROVIDER
        provider = db.query(User).filter(User.email == "provider@btt.com").first()
        if not provider:
            provider = User(
                email="provider@btt.com",
                hashed_password=get_password_hash("Provider@123"),
                full_name="Dr. Johnathan Hale",
                phone_number="+1-555-0104",
                role=UserRole.PROVIDER,
                account_status=AccountStatus.ACTIVE,
                is_verified=True,
                email_verified=True,
                is_active=True,
            )
            db.add(provider)
            db.flush()
            provider_profile = ProviderProfile(
                user_id=provider.id,
                professional_title="Licensed Clinical Psychologist",
                years_of_experience=12,
                bio="Specializing in trauma-informed CBT and mindfulness-based therapy for adults and adolescents.",
                specialties=["anxiety", "depression", "trauma", "ptsd"],
                modalities=["cbt", "emdr", "mindfulness"],
                languages=["English", "Spanish"],
                insurance_accepted=["Aetna", "BlueCross", "UnitedHealthcare"],
                office_address="123 Wellness Blvd, Suite 400, Hyderabad, Telangana 500081",
                latitude=17.3850,
                longitude=78.4867,
                timezone="Asia/Kolkata",
                accepting_new_clients=True,
                is_published=True,
                average_rating=4.8,
                total_reviews=47,
                profile_picture_url="https://btt.com/uploads/avatars/dr-hale.jpg",
            )
            db.add(provider_profile)
            db.flush()
            print("✅ Provider + ProviderProfile created")
        else:
            provider_profile = db.query(ProviderProfile).filter(ProviderProfile.user_id == provider.id).first()

        # CLIENT
        client = db.query(User).filter(User.email == "client@btt.com").first()
        if not client:
            client = User(
                email="client@btt.com",
                hashed_password=get_password_hash("Client@123"),
                full_name="Meera Patel",
                phone_number="+1-555-0105",
                role=UserRole.CLIENT,
                account_status=AccountStatus.ACTIVE,
                is_verified=True,
                email_verified=True,
                is_active=True,
            )
            db.add(client)
            db.flush()
            client_profile = ClientProfile(
                user_id=client.id,
                date_of_birth=datetime(1995, 6, 15, tzinfo=timezone.utc),
                gender="Female",
                pronouns="she/her",
                preferred_language="English",
                total_sessions=14,
                profile_picture_url="https://btt.com/uploads/avatars/meera.jpg",
            )
            db.add(client_profile)
            db.flush()
            print("✅ Client + ClientProfile created")
        else:
            client_profile = db.query(ClientProfile).filter(ClientProfile.user_id == client.id).first()

        # ===================================================================
        # 2. ORGANIZATION + MULTI-TENANCY
        # ===================================================================
        org = db.query(Organization).filter(Organization.slug == "btt-mental-health").first()
        if not org:
            org = Organization(
                name="BTT Mental Health Group",
                slug="btt-mental-health",
                legal_name="Better Therapy Together Pvt Ltd",
                tax_id="29AAECB1234A1Z5",
                email="admin@btt.com",
                phone_number="+91-40-12345678",
                website="https://btt.com",
                address_line1="Plot 45, Road No. 12, Banjara Hills",
                city="Hyderabad",
                state="Telangana",
                country="India",
                postal_code="500034",
                logo_url="https://btt.com/uploads/logo.png",
                status=OrgStatus.ACTIVE,
            )
            db.add(org)
            db.flush()
            print("✅ Organization created")

            # OrganizationMember links
            db.add(OrganizationMember(organization_id=org.id, user_id=super_admin.id, role_in_org="owner", is_active=True))
            db.add(OrganizationMember(organization_id=org.id, user_id=admin.id, role_in_org="manager", is_active=True))
            db.add(OrganizationMember(organization_id=org.id, user_id=executive.id, role_in_org="director", is_active=True))
            db.flush()

            # OrganizationSetting
            db.add(OrganizationSetting(
                organization_id=org.id,
                timezone="Asia/Kolkata",
                default_session_duration=50,
                allow_self_booking=True,
                require_approval_for_new_clients=False,
                custom_config={"welcome_message": "Welcome to BTT – your healing journey starts here."},
            ))

            # OrganizationBillingInfo
            db.add(OrganizationBillingInfo(
                organization_id=org.id,
                stripe_customer_id="cus_dummy_987654",
                billing_email="billing@btt.com",
                billing_address="Plot 45, Banjara Hills, Hyderabad",
                tax_id="29AAECB1234A1Z5",
            ))

            # OrganizationBranding
            db.add(OrganizationBranding(
                organization_id=org.id,
                primary_color="#0f766e",
                secondary_color="#14b8a6",
                logo_url="https://btt.com/uploads/logo.png",
                favicon_url="https://btt.com/uploads/favicon.ico",
            ))
            db.flush()
            print("✅ Organization settings, billing & branding created")

        # ===================================================================
        # 3. PROVIDER-SPECIFIC DATA
        # ===================================================================
        if not db.query(ProviderEducation).filter(ProviderEducation.provider_profile_id == provider_profile.id).first():
            db.add(ProviderEducation(
                provider_profile_id=provider_profile.id,
                degree="PsyD",
                institution="National Institute of Mental Health & Neurosciences (NIMHANS)",
                field_of_study="Clinical Psychology",
                graduation_year=2014,
                license_type="Licensed Clinical Psychologist",
                thesis_topic="Trauma Recovery in Urban Indian Populations",
            ))
            db.flush()
            print("✅ ProviderEducation created")

        if not db.query(ProviderAvailability).filter(ProviderAvailability.provider_id == provider_profile.id).first():
            for day in range(0, 5):  # Mon–Fri
                db.add(ProviderAvailability(
                    provider_id=provider_profile.id,
                    day_of_week=day,
                    start_time="09:00",
                    end_time="18:00",
                    is_recurring=True,
                ))
            db.flush()
            print("✅ ProviderAvailability created")

        if not db.query(ProviderLicense).filter(ProviderLicense.user_id == provider.id).first():
            db.add(ProviderLicense(
                user_id=provider.id,
                license_number="PSY-2020-45678",
                state="TG",
                expiry_date=utc_now() + timedelta(days=365 * 3),
                is_verified=True,
                verified_at=utc_now() - timedelta(days=180),
                verified_by=admin.id,
            ))
            db.flush()
            print("✅ ProviderLicense created")

        if not db.query(ProviderDocument).filter(ProviderDocument.user_id == provider.id).first():
            db.add(ProviderDocument(
                user_id=provider.id,
                file_url="https://btt.com/uploads/documents/dr-hale-license.pdf",
                file_type="pdf",
                original_filename="license-2024.pdf",
                verified=True,
            ))
            db.flush()
            print("✅ ProviderDocument created")

        if not db.query(ProviderReview).filter(ProviderReview.provider_id == provider_profile.id).first():
            db.add(ProviderReview(
                provider_id=provider_profile.id,
                client_id=client.id,
                rating=5.0,
                comment="Dr. Hale helped me overcome severe anxiety with practical tools. Highly recommend!",
            ))
            db.flush()
            print("✅ ProviderReview created")

        if not db.query(ProviderSubscription).filter(ProviderSubscription.provider_id == provider_profile.id).first():
            db.add(ProviderSubscription(
                provider_id=provider_profile.id,
                plan_name="Professional Tier",
                stripe_subscription_id="sub_dummy_provider_001",
                status="active",
                current_period_start=utc_now() - timedelta(days=30),
                current_period_end=utc_now() + timedelta(days=335),
            ))
            db.flush()
            print("✅ ProviderSubscription created")

        if not db.query(ProviderPublicationRequest).filter(ProviderPublicationRequest.provider_id == provider_profile.id).first():
            db.add(ProviderPublicationRequest(
                provider_id=provider_profile.id,
                status="APPROVED",
                requested_at=utc_now() - timedelta(days=45),
                reviewed_by=admin.id,
                reviewed_at=utc_now() - timedelta(days=40),
                reviewer_notes="All documents verified and profile complete.",
            ))
            db.flush()

        if not db.query(ProviderGallery).filter(ProviderGallery.provider_id == provider_profile.id).first():
            db.add(ProviderGallery(
                provider_id=provider_profile.id,
                file_url="https://btt.com/uploads/gallery/office-1.jpg",
                file_type="image",
                caption="My serene therapy space in Banjara Hills",
            ))
            db.flush()
            print("✅ ProviderGallery created")

        # ===================================================================
        # 4. CLIENT-SPECIFIC DATA
        # ===================================================================
        if not db.query(ClientSubscription).filter(ClientSubscription.client_id == client_profile.id).first():
            db.add(ClientSubscription(
                client_id=client_profile.id,
                plan_name="Monthly Premium",
                stripe_subscription_id="sub_dummy_client_001",
                status="active",
                expiry_date=utc_now() + timedelta(days=25),
                auto_renew=True,
            ))
            db.flush()
            print("✅ ClientSubscription created")

        if not db.query(ClientPreference).filter(ClientPreference.client_id == client_profile.id).first():
            db.add(ClientPreference(
                client_id=client_profile.id,
                notification_email=True,
                notification_sms=True,
                notification_push=True,
                preferred_language="English",
                preferred_modality="video",
                custom_preferences={"preferred_time": "evenings"},
            ))
            db.flush()

        if not db.query(ClientMedicalHistory).filter(ClientMedicalHistory.client_id == client_profile.id).first():
            db.add(ClientMedicalHistory(
                client_id=client_profile.id,
                conditions=["Generalized Anxiety Disorder", "Mild Depression"],
                medications=["Escitalopram 10mg daily"],
                allergies=["None known"],
                notes="No major medical conditions. Family history of anxiety.",
                last_updated_at=utc_now() - timedelta(days=60),
            ))
            db.flush()
            print("✅ ClientMedicalHistory created")

        if not db.query(ClientGoal).filter(ClientGoal.client_id == client_profile.id).first():
            goal = ClientGoal(
                client_id=client_profile.id,
                title="Reduce daily anxiety to manageable levels",
                description="Implement CBT techniques and mindfulness practice consistently.",
                target_date=utc_now() + timedelta(days=90),
                status="IN_PROGRESS",
            )
            db.add(goal)
            db.flush()

            db.add(ClientProgress(
                client_id=client_profile.id,
                goal_id=goal.id,
                progress_percentage=65.0,
                notes="Significant improvement in sleep and work focus after 6 sessions.",
                recorded_at=utc_now() - timedelta(days=15),
            ))
            db.flush()
            print("✅ ClientGoal + ClientProgress created")

        if not db.query(ClientAppointment).filter(ClientAppointment.client_id == client_profile.id).first():
            db.add(ClientAppointment(
                client_id=client_profile.id,
                provider_id=provider_profile.id,
                appointment_datetime=utc_now() + timedelta(days=7, hours=10),
                status="SCHEDULED",
                notes="Follow-up on anxiety management plan",
            ))
            db.add(ClientAppointment(
                client_id=client_profile.id,
                provider_id=provider_profile.id,
                appointment_datetime=utc_now() - timedelta(days=12),
                status="COMPLETED",
                notes="Excellent progress noted",
            ))
            db.flush()
            print("✅ ClientAppointment created")

        if not db.query(ClientTherapySession).filter(ClientTherapySession.client_id == client_profile.id).first():
            db.add(ClientTherapySession(
                client_id=client_profile.id,
                provider_id=provider_profile.id,
                session_date=utc_now() - timedelta(days=12),
                duration_minutes=50,
                notes="Discussed cognitive distortions and introduced breathing exercises.",
            ))
            db.flush()

        if not db.query(ClientNote).filter(ClientNote.client_id == client_profile.id).first():
            db.add(ClientNote(
                client_id=client_profile.id,
                title="Initial Intake Summary",
                content="Client presents with moderate GAD. Motivated for therapy. Recommended weekly sessions.",
                created_by=executive.id,
            ))
            db.flush()
            print("✅ ClientNote created")

        if not db.query(ClientJournalEntry).filter(ClientJournalEntry.client_id == client_profile.id).first():
            db.add(ClientJournalEntry(
                client_id=client_profile.id,
                title="Gratitude Journal - Week 3",
                content="Today I noticed my anxiety before a meeting but used the grounding technique successfully.",
                mood_rating=7,
            ))
            db.flush()

        # Minimal client supporting records
        if not db.query(ClientAllergy).filter(ClientAllergy.client_id == client_profile.id).first():
            db.add(ClientAllergy(client_id=client_profile.id, allergen="Penicillin", severity="Moderate", reaction="Hives and swelling", noted_at=utc_now() - timedelta(days=200)))
        if not db.query(ClientMedication).filter(ClientMedication.client_id == client_profile.id).first():
            db.add(ClientMedication(client_id=client_profile.id, medication_name="Escitalopram", dosage="10mg", frequency="once daily", prescribed_by="Dr. Anika Rao", start_date=utc_now() - timedelta(days=180)))
        if not db.query(ClientDocument).filter(ClientDocument.client_id == client_profile.id).first():
            db.add(ClientDocument(client_id=client_profile.id, file_url="https://btt.com/uploads/documents/meera-intake.pdf", file_type="pdf", original_filename="intake_form_signed.pdf", verified=True))
        if not db.query(ClientIntakeForm).filter(ClientIntakeForm.client_id == client_profile.id).first():
            db.add(ClientIntakeForm(client_id=client_profile.id, form_type="initial_assessment", responses={"q1": "Moderate anxiety", "q2": "Sleep issues", "q3": "Work stress"}, completed_at=utc_now() - timedelta(days=90)))
        if not db.query(ClientAssessment).filter(ClientAssessment.client_id == client_profile.id).first():
            db.add(ClientAssessment(client_id=client_profile.id, assessment_type="GAD-7", score=14, responses={"total": 14}, taken_at=utc_now() - timedelta(days=30)))
        if not db.query(ClientConsent).filter(ClientConsent.client_id == client_profile.id).first():
            db.add(ClientConsent(client_id=client_profile.id, consent_type="telehealth", version="v2.1", accepted=True, accepted_at=utc_now() - timedelta(days=90), ip_address="182.0.1.45"))
            db.flush()
            print("✅ All Client-related records created")

        # ===================================================================
        # 5. EXECUTIVE MODULE
        # ===================================================================
        exec_profile = db.query(ExecutiveProfile).filter(ExecutiveProfile.user_id == executive.id).first()
        if exec_profile and not db.query(ExecutivePermission).filter(ExecutivePermission.executive_id == exec_profile.id).first():
            db.add(ExecutivePermission(executive_id=exec_profile.id, permission="provider_onboarding"))
            db.add(ExecutivePermission(executive_id=exec_profile.id, permission="billing_view"))
            db.flush()

        if exec_profile and not db.query(ExecutiveActivityLog).filter(ExecutiveActivityLog.executive_id == exec_profile.id).first():
            db.add(ExecutiveActivityLog(
                executive_id=exec_profile.id,
                action="APPROVED_PROVIDER",
                entity_type="provider_profile",
                entity_id=provider_profile.id,
                details={"provider_name": "Dr. Johnathan Hale"},
                ip_address="127.0.0.1",
            ))
            db.flush()
            print("✅ ExecutivePermission + ExecutiveActivityLog created")

        if not db.query(ClinicStaff).filter(ClinicStaff.organization_id == org.id).first():
            db.add(ClinicStaff(
                organization_id=org.id,
                user_id=admin.id,
                role="receptionist",
                is_active=True,
                hired_at=utc_now() - timedelta(days=365),
            ))
            db.flush()

        if not db.query(ClinicAnnouncement).filter(ClinicAnnouncement.organization_id == org.id).first():
            db.add(ClinicAnnouncement(
                organization_id=org.id,
                title="New Telehealth Feature Live",
                content="All providers can now offer video sessions directly from the dashboard.",
                priority="high",
                expires_at=utc_now() + timedelta(days=30),
                created_by=executive.id,
            ))
            db.flush()
            print("✅ ClinicStaff + ClinicAnnouncement created")

        # ===================================================================
        # 6. AUTH & SECURITY MODULE
        # ===================================================================
        if not db.query(SystemSetting).filter(SystemSetting.key == "platform_name").first():
            settings = [
                {"key": "platform_name", "value": {"en": "BTT Mental Health"}, "description": "Platform display name"},
                {"key": "session_timeout_minutes", "value": 60, "description": "Idle timeout"},
                {"key": "allow_self_signup", "value": True, "description": "Client self-registration"},
            ]
            for s in settings:
                db.add(SystemSetting(**s, updated_by=super_admin.id))
            db.flush()
            print("✅ SystemSetting created")

        if not db.query(PasswordHistory).filter(PasswordHistory.user_id == client.id).first():
            db.add(PasswordHistory(
                user_id=client.id,
                hashed_password=get_password_hash("OldClientPass123"),
                changed_at=utc_now() - timedelta(days=180),
            ))
            db.flush()
            print("✅ PasswordHistory created")

        if not db.query(LoginAttempt).filter(LoginAttempt.email == "client@btt.com").first():
            db.add(LoginAttempt(
                email="client@btt.com",
                ip_address="182.0.1.45",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                success=True,
                attempted_at=utc_now() - timedelta(minutes=30),
                user_id=client.id,
            ))
            db.add(LoginAttempt(
                email="client@btt.com",
                ip_address="182.0.1.45",
                user_agent="Mozilla/5.0",
                success=False,
                attempted_at=utc_now() - timedelta(minutes=35),
            ))
            db.flush()
            print("✅ LoginAttempt created")

        if not db.query(BlacklistedToken).first():
            db.add(BlacklistedToken(
                jti="550e8400-e29b-41d4-a716-446655440000",
                user_id=client.id,
                expires_at=utc_now() + timedelta(hours=24),
            ))
            db.flush()

        if not db.query(UserMFABackupCode).filter(UserMFABackupCode.user_id == super_admin.id).first():
            db.add(UserMFABackupCode(
                user_id=super_admin.id,
                code_hash=get_password_hash("BACKUP123456"),
                used=False,
            ))
            db.flush()
            print("✅ BlacklistedToken + UserMFABackupCode created")

        # ===================================================================
        # 7. AUDIT & ACTIVITY LOGS
        # ===================================================================
        if not db.query(AdminActivityLog).filter(AdminActivityLog.performed_by_id == super_admin.id).first():
            db.add(AdminActivityLog(
                performed_by_id=super_admin.id,
                action="PUBLISH_PROVIDER",
                entity_type="provider_profile",
                entity_id=provider_profile.id,
                details={"reason": "All documents verified and profile meets quality standards"},
                ip_address="127.0.0.1",
            ))
            db.flush()
            print("✅ AdminActivityLog created")

        if not db.query(AuditLog).first():
            db.add(AuditLog(
                user_id=client.id,
                action="LOGIN",
                entity_type="user",
                entity_id=client.id,
                details={"ip": "182.0.1.45", "device": "web"},
                performed_by=super_admin.id,
                ip_address="182.0.1.45",
            ))
            db.flush()
            print("✅ AuditLog created")

        # ===================================================================
        # 8. OPTIONAL WAITLIST / INVITE
        # ===================================================================
        if not db.query(ProviderWaitlist).first():
            db.add(ProviderWaitlist(
                provider_id=provider_profile.id,
                client_id=client.id,
                requested_at=utc_now() - timedelta(days=5),
                notes="Looking for evening slots only",
            ))
            db.flush()

        if not db.query(OrganizationInvite).first():
            db.add(OrganizationInvite(
                organization_id=org.id,
                email="newprovider@btt.com",
                invited_by=executive.id,
                role_in_org="provider",
                token="invite-token-dummy-987654",
                expires_at=utc_now() + timedelta(days=7),
            ))
            db.flush()
            print("✅ ProviderWaitlist + OrganizationInvite created")

        db.commit()
        print("\n=== ✅ ALL DUMMY DATA LOADED SUCCESSFULLY ===\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Error loading dummy data: {e}")
        import traceback
        traceback.print_exc()
        raise

    finally:
        db.close()

if __name__ == "__main__":
    print("Ensuring tables exist...")
    Base.metadata.create_all(bind=engine)
    print("Tables successfully recreated.\n")

    load_dummy_data()