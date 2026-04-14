# app/modules/provider/services/registration_service.py
# import httpx
# import logging
# from sqlalchemy.orm import Session
# from fastapi import HTTPException, status
# from app.modules.provider.models.provider_registration import ProviderRegistration, RegistrationStatus
# from app.modules.users.models.user_model import User, UserRole, AccountStatus
# from app.utils.security import hash_password
# from app.utils.npi_validators import validate_npi # Assuming this is your Luhn check

# logger = logging.getLogger(__name__)

# class RegistrationService:
#     NPPES_URL = "https://npiregistry.cms.hhs.gov/api/"

#     @staticmethod
#     async def verify_npi_with_registry(npi: str, first_name: str, last_name: str):
#         """Step 2: Check NPPES Public Registry for Name and Active Status"""
#         params = {"number": npi, "version": "2.1"}
#         async with httpx.AsyncClient(timeout=10.0) as client:
#             try:
#                 response = await client.get(RegistrationService.NPPES_URL, params=params)
#                 if response.status_code != 200:
#                     return False, "NPI Registry temporarily unavailable"
                
#                 data = response.json()
#                 if data.get("result_count", 0) == 0:
#                     return False, "NPI not found in public registry"
                
#                 result = data["results"][0]
#                 # Check if Active
#                 if result.get("status") != "A":
#                     return False, "NPI status is not Active in registry"
                
#                 # Check Name Match (Case Insensitive)
#                 reg_first = result["basic"].get("first_name", "").upper()
#                 reg_last = result["basic"].get("last_name", "").upper()
                
#                 if reg_first != first_name.upper() or reg_last != last_name.upper():
#                     return False, f"Name mismatch. Registry shows: {reg_first} {reg_last}"
                
#                 return True, "Verified"
#             except Exception as e:
#                 logger.error(f"NPPES API Error: {str(e)}")
#                 return False, "Error connecting to NPI registry"

#     @staticmethod
#     async def create_registration(db: Session, registration_data: dict):
#         # 1. Step 1: Luhn Algorithm (Local Check)
#         if not validate_npi(registration_data["npi_number"]):
#             raise HTTPException(status_code=400, detail="Invalid NPI number format")

#         # 2. Step 2: NPPES Registry Check (External API)
#         is_valid, msg = await RegistrationService.verify_npi_with_registry(
#             registration_data["npi_number"], 
#             registration_data["first_name"], 
#             registration_data["last_name"]
#         )
#         if not is_valid:
#             raise HTTPException(status_code=400, detail=msg)

#         # 3. Check if email already exists
#         if db.query(User).filter(User.email == registration_data["email"]).first():
#             raise HTTPException(status_code=400, detail="Email already registered")

#         try:
#             # 4. Create User (Atomic Transaction)
#             user = User(
#                 email=registration_data["email"],
#                 hashed_password=hash_password(registration_data.pop("password")),
#                 full_name=f"{registration_data['first_name']} {registration_data['last_name']}",
#                 role=UserRole.PROVIDER,
#                 account_status=AccountStatus.PENDING
#             )
#             db.add(user)
#             db.flush() # Get user.id without committing yet

#             # 5. Create Registration
#             registration = ProviderRegistration(
#                 user_id=user.id,
#                 **registration_data,
#                 npi_validated=True,
#                 status=RegistrationStatus.PENDING_ADMIN_REVIEW
#             )
#             db.add(registration)
            
#             db.commit() # Commit both User and Registration together
#             db.refresh(registration)

#             return {
#                 "registration_id": str(registration.id),
#                 "status": registration.status.value,
#                 "message": "Registration submitted. Pending admin review of state license."
#             }
#         except Exception as e:
#             db.rollback()
#             logger.error(f"Registration DB Error: {str(e)}")
#             raise HTTPException(status_code=500, detail="Internal server error")

import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets
from app.core.email import EmailService
from app.modules.provider.models.provider_registration import ProviderRegistration, RegistrationStatus
from app.modules.users.models.user_model import User, UserRole, AccountStatus
from app.modules.auth.services.auth_service import AuthService
from app.utils.npi_validators import validate_npi_luhn
from .npi_registry_service import NPIRegistryService 
from .payment_service import PaymentGatewayService
from datetime import datetime, timezone, timedelta
logger = logging.getLogger(__name__)

# class RegistrationService:
#     @staticmethod
#     async def create_registration(db: Session, registration_data: dict):
#         # 1. Extract fields for validation
#         npi_number = registration_data.get("npi_number")
#         email = registration_data.get("email")
#         first_name = registration_data.get("first_name")
#         last_name = registration_data.get("last_name")

#         # 2. Step 1: Local Luhn Check
#         if not validate_npi_luhn(npi_number):
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST, 
#                 detail="Invalid NPI number format (Luhn check failed)."
#             )

#         # 3. Step 2: External NPPES Registry Check
#         is_valid, msg = await NPIRegistryService.verify_npi_data(
#             npi=npi_number, 
#             first_name=first_name, 
#             last_name=last_name
#         )
#         if not is_valid:
#             raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

#         # 4. Step 3: Duplicate Checks
#         if db.query(User).filter(User.email == email).first():
#             raise HTTPException(status_code=400, detail="A user with this email already exists.")
        
#         if db.query(ProviderRegistration).filter(ProviderRegistration.npi_number == npi_number).first():
#             raise HTTPException(status_code=400, detail="This NPI number is already associated with an account.")
        
#         password = registration_data.pop("password")
#         billing_token = registration_data.pop("billing_token", "token_placeholder")
#         payment_method_id = registration_data.pop("payment_method_id", None)
#         token_to_use = billing_token or payment_method_id or "token_placeholder"
#         try:
#             # 5. Step 4: Atomic Transaction
#             # Pop password so it's not passed into the ProviderRegistration model
            
#             customer_id, sub_id = await PaymentGatewayService.initialize_subscription(
#                 email=registration_data["email"],
#                 full_name=f"{registration_data['first_name']} {registration_data['last_name']}",
#                 token=token_to_use
#             )
#             # raw_password = registration_data.pop("password")
            
#             user = User(
#                 email=email,
#                 hashed_password=get_password_hash(password),
#                 full_name=f"{first_name} {last_name}",
#                 role=UserRole.PROVIDER,
#                 account_status=AccountStatus.PENDING,
#                 is_verified=False,
#                 is_active=True
#             )
#             db.add(user)
#             verification_token = secrets.token_urlsafe(32)
#             user.verification_code = verification_token
#             user.verification_code_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
#             db.flush() 

#             # Create Registration Record
#             # NOTE: registration_data must contain address, licensing_board, etc. 
#             # and the Model MUST have those columns.
#             registration = ProviderRegistration(
#                 user_id=user.id,
#                 **registration_data,
#                 billing_customer_id=customer_id,
#                 billing_subscription_id=sub_id,
#                 billing_status="trialing",
#                 npi_validated=True,
#                 status=RegistrationStatus.PENDING_ADMIN_REVIEW.value # Use .value for String column
#             )
#             db.add(registration)
            
#             db.commit() 
#             db.refresh(registration)

#             logger.info(f"Provider registration successful for {email}.")
            
#             await EmailService.send_verification_email(user.email, user.verification_code)
#             return {
#                 "registration_id": str(registration.id),
#                 "status": registration.status, # REMOVED .value (it's already a string)
#                 "message": "Registration submitted. Our team will verify your state license shortly."
#             }

#         except Exception as e:
#             db.rollback()
#             logger.error(f"Critical Registration Error: {str(e)}")
#             # Provide a cleaner error message for the frontend
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
#                 detail="An internal error occurred. Please ensure all fields are correct."
#             )
class RegistrationService:
    @staticmethod
    async def create_registration(db: Session, registration_data: dict):
        # 1. Extract fields
        npi_number = registration_data.get("npi_number")
        npi_type = registration_data.get("npi_type")
        email = registration_data.get("email")
        first_name = registration_data.get("first_name")
        last_name = registration_data.get("last_name")
        password = registration_data.pop("password")
        registration_data.pop("confirm_password") # Remove confirm_password
        phone_number = registration_data.pop("phone_number", None) 
        # 2. NPI Validation (If this fails, he cannot register/login)
        is_valid, msg = await NPIRegistryService.verify_npi_data(
            npi=npi_number, 
            first_name=first_name, 
            last_name=last_name,
            npi_type=npi_type
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

        # 3. Duplicate Checks
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        try:
            # 4. Create User (PENDING status)
            user = User(
                email=email,
                hashed_password=AuthService.get_password_hash(password),
                full_name=f"{first_name} {last_name}",
                phone_number=phone_number,
                role=UserRole.PROVIDER,
                account_status=AccountStatus.PENDING, # Cannot login yet
                is_verified=False
            )
            
            # 5. Generate Email Verification Token
            verification_token = secrets.token_urlsafe(32)
            user.verification_code = verification_token
            user.verification_code_expiry = datetime.now(timezone.utc) + timedelta(hours=24)
            
            db.add(user)
            db.flush() 

            # 6. Create Registration Record
            registration = ProviderRegistration(
                user_id=user.id,
                **registration_data,
                npi_validated=True,
                status=RegistrationStatus.PENDING_ADMIN_REVIEW.value
            )
            db.add(registration)
            db.commit() 

            # 7. Send Verification Email
            await EmailService.send_verification_email(user.email, verification_token)

            return {
                "registration_id": str(registration.id),
                "message": "Registration successful. Please verify your email to proceed."
            }
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
