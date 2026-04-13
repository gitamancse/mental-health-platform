from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone
import logging

from app.modules.provider.models.provider_registration import ProviderRegistration, RegistrationStatus
from app.modules.provider.models.admin_action import AdminAction, ActionType
from app.modules.users.models.user_model import User, ProviderProfile, AccountStatus
from uuid import UUID
logger = logging.getLogger(__name__)

def approve_registration(db: Session, registration_id: str, admin_id: str, proof_url: str, admin_notes: str = None):
    """
    Approves a provider, activates their account, and creates their clinical profile.
    """
    registration = db.query(ProviderRegistration).filter(ProviderRegistration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    user = db.query(User).filter(User.id == registration.user_id).first()
    
    try:
        # 1. Update Registration
        registration.status = RegistrationStatus.APPROVED
        registration.reviewed_by = admin_id
        registration.reviewed_at = datetime.now(timezone.utc)
        registration.license_proof_url = proof_url
        registration.admin_notes = admin_notes

        # 2. Activate User
        user.account_status = AccountStatus.ACTIVE
        user.is_verified = True

        # 3. Create Profile (Enables provider dashboard access)
        new_profile = ProviderProfile(
            user_id=user.id,
            professional_title=registration.professional_role,
            profile_status="draft",
            is_published=False
        )
        db.add(new_profile)

        # 4. Audit Log
        action = AdminAction(
            admin_id=admin_id,
            user_id=registration.user_id,
            action_type=ActionType.APPROVE_REGISTRATION,
            target_id=registration.id,
            target_type="provider_registration",
            action_metadata={"proof_url": proof_url, "notes": admin_notes}
        )
        db.add(action)

        db.commit()
        return {"status": "success", "message": "Provider approved and profile initialized."}

    except Exception as e:
        db.rollback()
        logger.error(f"Approval Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during approval")

def reject_registration(db: Session, registration_id: str, admin_id: str, reason: str):
    """
    Rejects a provider registration and logs the reason for audit compliance.
    """
    registration = db.query(ProviderRegistration).filter(ProviderRegistration.id == registration_id).first()
    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    try:
        # 1. Update Registration Status
        registration.status = RegistrationStatus.REJECTED
        registration.rejection_reason = reason
        registration.reviewed_by = admin_id
        registration.reviewed_at = datetime.now(timezone.utc)

        # 2. Audit Log (Required for HIPAA/SOC2)
        action = AdminAction(
            admin_id=admin_id,
            user_id=registration.user_id,
            action_type=ActionType.REJECT_REGISTRATION,
            target_id=registration.id,
            target_type="provider_registration",
            action_metadata={"rejection_reason": reason}
        )
        db.add(action)

        db.commit()
        logger.info(f"Admin {admin_id} rejected registration {registration_id}. Reason: {reason}")
        
        return {"status": "success", "message": "Registration rejected successfully."}

    except Exception as e:
        db.rollback()
        logger.error(f"Rejection Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during rejection")


def manual_npi_override(db: Session, registration_id: UUID, admin_id: UUID, reason: str):
    """
    Manually validates a provider's NPI when the automated check fails.
    Required for HIPAA audit compliance.
    """
    # 1. Fetch Registration
    registration = db.query(ProviderRegistration).filter(
        ProviderRegistration.id == registration_id
    ).first()

    if not registration:
        raise HTTPException(status_code=404, detail="Registration not found")

    try:
        # 2. Update Registration Record
        registration.admin_override = True
        registration.override_reason = reason
        registration.npi_validated = True  # We force this to True so the final approval can proceed

        # 3. Log the specific Override Action (Audit Trail)
        # Using ActionType.MANUAL_NPI_OVERRIDE if you have it in your Enum
        action = AdminAction(
            admin_id=admin_id,
            user_id=registration.user_id,
            action_type="manual_npi_override", 
            target_id=registration.id,
            target_type="provider_registration",
            action_metadata={"reason": reason}
        )
        db.add(action)
        
        db.commit()
        logger.info(f"Admin {admin_id} performed NPI override for registration {registration_id}")

        return {
            "status": "success", 
            "message": "NPI validation manually overridden. You may now proceed with approval."
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Override Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during override")