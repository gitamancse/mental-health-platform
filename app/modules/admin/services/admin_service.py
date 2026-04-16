from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timezone
import logging
from typing import Optional, Dict
from app.modules.provider.models.provider_registration import ProviderRegistration, RegistrationStatus
from app.modules.admin.models.admin_action import AdminAction, ActionType
from app.modules.users.models.user_model import User, AccountStatus
from app.modules.provider.models.provider_model import ProviderProfile
from uuid import UUID
from sqlalchemy import desc
from app.modules.admin.schemas.admin_schema import (
    ProviderRegistrationListItem,
    ProviderRegistrationDetailResponse,
    LicenseVerificationInfo
)

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
    
# License Verification
class LicenseVerificationService:
    """Service layer with all 50 US states for therapist license verification"""

    _STATE_DATA: Dict[str, Dict] = {
        "AL": {
            "name": "Alabama",
            "licensing_board": "Alabama Board of Examiners in Counseling",
            "url": "https://dashboard.albme.gov/Verification/search.aspx"
        },
        "AK": {
            "name": "Alaska",
            "licensing_board": "Alaska Board of Professional Counselors",
            "url": "https://www.commerce.alaska.gov/cbp/main/Search/Professional"
        },
        "AZ": {
            "name": "Arizona",
            "licensing_board": "Arizona Board of Behavioral Health Examiners",
            "url": "https://azbbhe.portalus.thentiacloud.net/webs/portal/register/#/"
        },
        "AR": {
            "name": "Arkansas",
            "licensing_board": "Arkansas Board of Examiners in Counseling",
            "url": "https://search.statesolutions.us/?A=ATRB&AID=RS"
        },
        "CA": {
            "name": "California",
            "licensing_board": "California Board of Behavioral Sciences",
            "url": "None"
        },
        "CO": {
            "name": "Colorado",
            "licensing_board": "Colorado DORA - Mental Health",
            "url": "https://apps2.colorado.gov/dora/licensing/lookup/licenselookup.aspx"
        },
        "CT": {
            "name": "Connecticut",
            "licensing_board": "Connecticut Department of Public Health",
            "url": "https://elicense.ct.gov/Lookup/LicenseLookup.aspx"
        },
        "DE": {
            "name": "Delaware",
            "licensing_board": "Delaware Board of Mental Health Counselors",
            "url": "https://dpronline.delaware.gov/mylicense%20weblookup/Search.aspx"
        },
        "FL": {
            "name": "Florida",
            "licensing_board": "Florida Board of Mental Health Counseling",
            "url": "https://mqa-internet.doh.state.fl.us/mqasearchservices/healthcareproviders"
        },
        "GA": {
            "name": "Georgia",
            "licensing_board": "Georgia Composite Board of Professional Counselors",
            "url": "https://goals.sos.ga.gov/GASOSOneStop/s/licensee-search"
        },
        "HI": {
            "name": "Hawaii",
            "licensing_board": "Hawaii Board of Mental Health Counselors",
            "url": "https://mypvl.dcca.hawaii.gov/public-license-search/"
        },
        "ID": {
            "name": "Idaho",
            "licensing_board": "Idaho Licensing Board of Professional Counselors",
            "url": "https://dopl.idaho.gov/cou/"
        },
        "IL": {
            "name": "Illinois",
            "licensing_board": "Illinois Department of Financial and Professional Regulation",
            "url": "https://online-dfpr.micropact.com/lookup/licenselookup.aspx"
        },
        "IN": {
            "name": "Indiana",
            "licensing_board": "Indiana Professional Licensing Agency",
            "url": "None"
        },
        "IA": {
            "name": "Iowa",
            "licensing_board": "Iowa Board of Behavioral Science",
            "url": "https://ia-plb.my.site.com/LicenseSearchPage"
        },
        "KS": {
            "name": "Kansas",
            "licensing_board": "Kansas Behavioral Sciences Regulatory Board",
            "url": "https://prolicenseverify.ks.gov/"
        },
        "KY": {
            "name": "Kentucky",
            "licensing_board": "Kentucky Board of Licensed Professional Counselors",
            "url": "https://oop.ky.gov/"
        },
        "LA": {
            "name": "Louisiana",
            "licensing_board": "Louisiana Licensed Professional Counselors Board",
            "url": "https://online.lasbme.org/#/verifylicense"
        },
        "ME": {
            "name": "Maine",
            "licensing_board": "Maine Board of Counseling Professionals Licensure",
            "url": "https://www.pfr.maine.gov/almsonline/almsquery/SearchIndividual.aspx"
        },
        "MD": {
            "name": "Maryland",
            "licensing_board": "Maryland Board of Professional Counselors & Therapists",
            "url": "https://mdbnc.health.maryland.gov/pctverification/default.aspx"
        },
        "MA": {
            "name": "Massachusetts",
            "licensing_board": "Massachusetts Board of Mental Health Counselors",
            "url": "https://elicensing21.mass.gov/CitizenAccess/GeneralProperty/PropertyLookUp.aspx?isLicensee=Y"
        },
        "MI": {
            "name": "Michigan",
            "licensing_board": "Michigan Board of Counseling",
            "url": "https://aca-prod.accela.com/MILARA/GeneralProperty/PropertyLookUp.aspx?isLicensee=Y"
        },
        "MN": {
            "name": "Minnesota",
            "licensing_board": "Minnesota Board of Behavioral Health",
            "url": "https://bht.hlb.state.mn.us/#/onlineEntitySearch"
        },
        "MS": {
            "name": "Mississippi",
            "licensing_board": "Mississippi Board of Examiners for Licensed Professional Counselors",
            "url": "https://www.lpc.ms.gov/secure/licensesearch.asp"
        },
        "MO": {
            "name": "Missouri",
            "licensing_board": "Missouri Committee for Professional Counselors",
            "url": "https://mopro.mo.gov/license/s/license-search"
        },
        "MT": {
            "name": "Montana",
            "licensing_board": "Montana Board of Behavioral Health",
            "url": "https://ebizws.mt.gov/PUBLICPORTAL/searchform?mylist=licenses"
        },
        "NE": {
            "name": "Nebraska",
            "licensing_board": "Nebraska Board of Mental Health Practice",
            "url": "None"
        },
        "NV": {
            "name": "Nevada",
            "licensing_board": "Nevada Board of Examiners for Marriage & Family Therapists & Clinical Professional Counselors",
            "url": "https://nvboe.certemy.com/public-registry/00b35480-36a9-4898-a052-c13871cce91e"
        },
        "NH": {
            "name": "New Hampshire",
            "licensing_board": "New Hampshire Board of Mental Health Practice",
            "url": "https://forms.nh.gov/licenseverification/"
        },
        "NJ": {
            "name": "New Jersey",
            "licensing_board": "New Jersey Professional Counselor Examiners Committee",
            "url": "https://newjersey.mylicense.com/verification/Search.aspx"
        },
        "NM": {
            "name": "New Mexico",
            "licensing_board": "New Mexico Regulation & Licensing Department",
            "url": "https://nmrldlpi.my.site.com/bcd/s/rld-public-search"
        },
        "NY": {
            "name": "New York",
            "licensing_board": "New York State Office of the Professions",
            "url": "https://eservices.nysed.gov/professions/verification-search"
        },
        "NC": {
            "name": "North Carolina",
            "licensing_board": "North Carolina Board of Licensed Clinical Mental Health Counselors",
            "url": "https://portal.ncblcmhc.org/verification/search.aspx"
        },
        "ND": {
            "name": "North Dakota",
            "licensing_board": "North Dakota Board of Counselor Examiners",
            "url": "None"
        },
        "OH": {
            "name": "Ohio",
            "licensing_board": "Ohio Counselor, Social Worker & Marriage & Family Therapist Board",
            "url": "https://elicense.ohio.gov/oh_verifylicense"
        },
        "OK": {
            "name": "Oklahoma",
            "licensing_board": "Oklahoma Board of Behavioral Health",
            "url": "https://obbhl.us.thentiacloud.net/webs/obbhl/register/#/"
        },
        "OR": {
            "name": "Oregon",
            "licensing_board": "Oregon Board of Licensed Professional Counselors & Therapists",
            "url": "https://omb.oregon.gov/search"
        },
        "PA": {
            "name": "Pennsylvania",
            "licensing_board": "Pennsylvania State Board of Social Workers, Marriage & Family Therapists",
            "url": "https://www.pa.gov/services/dos/verify-a-professional-or-occupational-license"
        },
        "RI": {
            "name": "Rhode Island",
            "licensing_board": "Rhode Island Department of Health",
            "url": "https://healthri.mylicense.com/verification/"
        },
        "SC": {
            "name": "South Carolina",
            "licensing_board": "South Carolina Board of Examiners in Psychology",
            "url": "None"
        },
        "SD": {
            "name": "South Dakota",
            "licensing_board": "South Dakota Board of Counselors & Marriage & Family Therapists",
            "url": "https://www.sdbmoe.gov/sdbmoe-licensee-lookup/"
        },
        "TN": {
            "name": "Tennessee",
            "licensing_board": "Tennessee Board of Professional Counselors",
            "url": "None"
        },
        "TX": {
            "name": "Texas",
            "licensing_board": "Texas Behavioral Health Executive Council",
            "url": "None"
        },
        "UT": {
            "name": "Utah",
            "licensing_board": "Utah Division of Occupational & Professional Licensing",
            "url": "https://secure.utah.gov/llv/search/index.html#"
        },
        "VT": {
            "name": "Vermont",
            "licensing_board": "Vermont Office of Professional Regulation",
            "url": "None"
        },
        "VA": {
            "name": "Virginia",
            "licensing_board": "Virginia Board of Counseling",
            "url": "https://dhp.virginiainteractive.org/lookup/index"
        },
        "WA": {
            "name": "Washington",
            "licensing_board": "Washington Department of Health",
            "url": "https://professions.dol.wa.gov/s/license-lookup"
        },
        "WV": {
            "name": "West Virginia",
            "licensing_board": "West Virginia Board of Examiners in Counseling",
            "url": "https://wvbec.org/counselor-and-therapist-license-verification/"
        },
        "WI": {
            "name": "Wisconsin",
            "licensing_board": "Wisconsin Department of Safety & Professional Services",
            "url": "https://license.wi.gov/s/license-lookup"
        },
        "WY": {
            "name": "Wyoming",
            "licensing_board": "Wyoming Mental Health Professions Licensing Board",
            "url": "https://mentalhealth.wyo.gov/public/license-verification"
        }
    }

    _NAME_TO_CODE: Dict[str, str] = {
        "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
        "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
        "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
        "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
        "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
        "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
        "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV",
        "new hampshire": "NH", "new jersey": "NJ", "new mexico": "NM", "new york": "NY",
        "north carolina": "NC", "north dakota": "ND", "ohio": "OH", "oklahoma": "OK",
        "oregon": "OR", "pennsylvania": "PA", "rhode island": "RI",
        "south carolina": "SC", "south dakota": "SD", "tennessee": "TN", "texas": "TX",
        "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
        "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
    }

    @staticmethod
    def get_state_verification(state_input: str) -> dict:
        if not state_input or not isinstance(state_input, str):
            return {
                "success": False,
                "state": "",
                "licensing_board": None,
                "verification_url": None,
                "message": "State parameter is required"
            }

        normalized = state_input.strip().lower()

        # Handle 2-letter code
        if len(normalized) == 2 and normalized.isalpha():
            code = normalized.upper()
        else:
            code = LicenseVerificationService._NAME_TO_CODE.get(normalized)

        if code not in LicenseVerificationService._STATE_DATA:
            return {
                "success": False,
                "state": state_input,
                "licensing_board": None,
                "verification_url": None,
                "message": f"Invalid state name or code: {state_input}"
            }

        data = LicenseVerificationService._STATE_DATA[code]
        url = data.get("url")

        return {
            "success": True,
            "state": data["name"],
            "licensing_board": data["licensing_board"],
            "verification_url": url if url and url != "None" else None,
            "message": "Click the link above to verify the therapist's license" if url else 
                       "No direct online portal available. Please contact the licensing board directly."
        }

# ====================== ADMIN SERVICE ======================
class AdminService:

    @staticmethod
    def get_pending_registrations(
        db: Session,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status_filter: Optional[str] = None,   # renamed for clarity
        state_filter: Optional[str] = None      # this should be used for license_state
    ) -> Dict:
        try:
            query = db.query(ProviderRegistration)

            # Status filter
            if not status_filter:
                query = query.filter(
                    ProviderRegistration.status.in_([
                        RegistrationStatus.PENDING_ADMIN_REVIEW.value,
                        RegistrationStatus.REQUEST_REVISIONS.value
                    ])
                )
            else:
                query = query.filter(ProviderRegistration.status == status_filter)

            # Search filter
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    (ProviderRegistration.first_name.ilike(search_term)) |
                    (ProviderRegistration.last_name.ilike(search_term)) |
                    (ProviderRegistration.email.ilike(search_term))
                )

            # State / License State filter
            if state_filter:
                query = query.filter(
                    ProviderRegistration.license_state == state_filter.upper()
                )

            total = query.count()
            registrations = query.order_by(desc(ProviderRegistration.submitted_at))\
                                .offset((page - 1) * limit)\
                                .limit(limit).all()

            # Convert to schema
            data_list = []
            for reg in registrations:
                item_data = {
                    "id": reg.id,
                    "first_name": reg.first_name,
                    "last_name": reg.last_name,
                    "email": reg.email,
                    "npi_number": reg.npi_number,
                    "npi_type": reg.npi_type,
                    "status": reg.status,
                    "submitted_at": reg.submitted_at,
                    "npi_validated": reg.npi_validated,
                    "admin_override": reg.admin_override,
                    "state": reg.license_state,   # Use license_state here
                    "city": reg.city
                }
                data_list.append(ProviderRegistrationListItem.model_validate(item_data))

            return {
                "data": data_list,
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": total,
                    "total_pages": (total + limit - 1) // limit
                }
            }

        except Exception as e:
            logger.error(f"Error in get_pending_registrations: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail="Failed to fetch registrations")


    @staticmethod
    def get_registration_detail(db: Session, registration_id: UUID) -> ProviderRegistrationDetailResponse:
        try:
            registration = db.query(ProviderRegistration).filter(
                ProviderRegistration.id == registration_id
            ).first()

            if not registration:
                raise HTTPException(status_code=404, detail="Provider registration not found")

            # Get license verification info
            license_info = LicenseVerificationService.get_state_verification(registration.license_state or "")

            license_verification = LicenseVerificationInfo(
                state=license_info.get("state", ""),
                licensing_board=license_info.get("licensing_board"),
                verification_url=license_info.get("verification_url"),
                message=license_info.get("message", ""),
                success=license_info.get("success", False)
            )

            # Manually build the data with computed fields
            data = {
                **registration.__dict__,
                "full_name": f"{registration.first_name or ''} {registration.last_name or ''}".strip(),
                "license_verification": license_verification
            }

            detail = ProviderRegistrationDetailResponse.model_validate(data)
            return detail

        except Exception as e:
            logger.error(f"Error in get_registration_detail: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error fetching detail: {str(e)}")


    @staticmethod
    def approve_registration(
        db: Session,
        registration_id: UUID,
        admin_id: UUID,
        proof_url: str,
        admin_notes: Optional[str] = None
    ):
        """
        Approves provider, activates user, and creates the ProviderProfile.
        """
        registration = db.query(ProviderRegistration).filter(ProviderRegistration.id == registration_id).first()
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")

        user = db.query(User).filter(User.id == registration.user_id).first()
        
        try:
            # 1. Update Registration
            registration.status = RegistrationStatus.APPROVED.value
            registration.reviewed_by = admin_id
            registration.reviewed_at = datetime.now(timezone.utc)
            registration.license_proof_url = proof_url
            registration.admin_notes = admin_notes

            # 2. Activate User
            user.account_status = AccountStatus.ACTIVE
            user.is_verified = True

            # 3. Create Profile (This allows the provider to start adding licenses)
            new_profile = ProviderProfile(
                user_id=user.id,
                professional_title=registration.title or "Provider",
                profile_status="draft",
                is_published=False
            )
            db.add(new_profile)

            # 4. Audit Log
            action = AdminAction(
                admin_id=admin_id,
                user_id=registration.user_id,
                action_type=ActionType.APPROVE_REGISTRATION.value,
                target_id=registration.id,
                target_type="provider_registration",
                action_metadata={"proof_url": proof_url, "notes": admin_notes}
            )
            db.add(action)

            db.commit()
            return {"status": "success", "message": "Provider approved and profile created."}

        except Exception as e:
            db.rollback()
            logger.error(f"Approval Error: {str(e)}")
            raise HTTPException(status_code=500, detail="Internal server error during approval")

    @staticmethod
    def reject_registration(db: Session, registration_id: UUID, admin_id: UUID, reason: str):
        registration = db.query(ProviderRegistration).filter(ProviderRegistration.id == registration_id).first()
        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")

        try:
            registration.status = RegistrationStatus.REJECTED.value
            registration.rejection_reason = reason
            registration.reviewed_by = admin_id
            registration.reviewed_at = datetime.now(timezone.utc)

            action = AdminAction(
                admin_id=admin_id,
                user_id=registration.user_id,
                action_type=ActionType.REJECT_REGISTRATION.value,
                target_id=registration.id,
                target_type="provider_registration",
                action_metadata={"rejection_reason": reason}
            )
            db.add(action)
            db.commit()
            return {"status": "success", "message": "Registration rejected."}
        except Exception as e:
            db.rollback()
            logger.error(f"Reject error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to reject")


    @staticmethod
    def request_revisions(
        db: Session,
        registration_id: UUID,
        admin_id: UUID,
        feedback: str
    ):
        """Request revisions from provider"""
        registration = db.query(ProviderRegistration).filter(
            ProviderRegistration.id == registration_id
        ).first()

        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")

        try:
            registration.status = RegistrationStatus.REQUEST_REVISIONS.value
            registration.admin_notes = feedback
            registration.reviewed_by = admin_id
            registration.reviewed_at = datetime.utcnow()

            action = AdminAction(
                admin_id=admin_id,
                user_id=registration.user_id,
                action_type=ActionType.REQUEST_REVISIONS.value,
                target_id=registration.id,
                target_type="provider_registration",
                action_metadata={"feedback": feedback}
            )
            db.add(action)

            db.commit()

            return {"status": "success", "message": "Revision request sent to provider."}

        except Exception as e:
            db.rollback()
            logger.error(f"Request revisions error: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to request revisions")


    @staticmethod
    def list_all_providers(
        db: Session,
        page: int = 1,
        limit: int = 20,
        status: Optional[str] = None
    ) -> Dict:
        """List all providers with optional status filter"""
        query = db.query(ProviderRegistration)

        if status:
            query = query.filter(ProviderRegistration.status == status)

        total = query.count()
        providers = query.order_by(desc(ProviderRegistration.submitted_at))\
                         .offset((page - 1) * limit)\
                         .limit(limit).all()

        data_list = []
        for reg in providers:
            reg_dict = {
                **reg.__dict__,
                "full_name": f"{reg.first_name or ''} {reg.last_name or ''}".strip()
            }
            data_list.append(ProviderRegistrationListItem.model_validate(reg_dict))

        return {
            "data": data_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        }


    @staticmethod
    def update_status(
        db: Session,
        registration_id: UUID,
        new_status: str,
        admin_id: UUID,
        notes: Optional[str] = None
    ):
        """Manually update status using PUT"""
        registration = db.query(ProviderRegistration).filter(
            ProviderRegistration.id == registration_id
        ).first()

        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")

        try:
            registration.status = new_status
            if notes:
                registration.admin_notes = notes

            action = AdminAction(
                admin_id=admin_id,
                user_id=registration.user_id,
                action_type="status_updated",
                target_id=registration.id,
                target_type="provider_registration",
                action_metadata={"new_status": new_status, "notes": notes}
            )
            db.add(action)

            db.commit()
            db.refresh(registration)

            return {"status": "success", "message": f"Status updated to {new_status}"}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to update status")


    @staticmethod
    def suspend_provider(
        db: Session,
        registration_id: UUID,
        admin_id: UUID,
        reason: str
    ):
        registration = db.query(ProviderRegistration).filter(
            ProviderRegistration.id == registration_id
        ).first()

        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")

        try:
            registration.status = "suspended"
            registration.admin_notes = f"Suspended: {reason}"

            action = AdminAction(
                admin_id=admin_id,
                user_id=registration.user_id,
                action_type="suspend",
                target_id=registration.id,
                target_type="provider_registration",
                action_metadata={"reason": reason}
            )
            db.add(action)

            db.commit()

            return {"status": "success", "message": "Provider suspended successfully."}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to suspend provider")


    @staticmethod
    def unpublish_provider(
        db: Session,
        registration_id: UUID,
        admin_id: UUID,
        reason: Optional[str] = None
    ):
        registration = db.query(ProviderRegistration).filter(
            ProviderRegistration.id == registration_id
        ).first()

        if not registration:
            raise HTTPException(status_code=404, detail="Registration not found")

        try:
            registration.is_published = False   # Make sure this column exists in model

            action = AdminAction(
                admin_id=admin_id,
                user_id=registration.user_id,
                action_type="unpublish",
                target_id=registration.id,
                target_type="provider_registration",
                action_metadata={"reason": reason}
            )
            db.add(action)

            db.commit()

            return {"status": "success", "message": "Provider profile unpublished successfully."}

        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to unpublish provider")