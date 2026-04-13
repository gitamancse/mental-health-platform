import sys
import os
from datetime import datetime, timedelta, timezone

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
from app.modules.auth.services.auth_service import get_password_hash


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

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
            )
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
    print("=== Resetting Database for Fresh Dummy Data ===")
    reset_database_completely()
    print("Dropping ALL existing tables...")
    Base.metadata.drop_all(bind=engine)
    print("Creating ALL tables from current models (this includes the new profile_picture_url columns)...")
    Base.metadata.create_all(bind=engine)
    print("Tables successfully recreated.\n")

    load_dummy_data()