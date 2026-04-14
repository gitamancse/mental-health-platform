# from pydantic import BaseModel, EmailStr, Field
# from typing import Optional
# from uuid import UUID

# class ProviderRegistrationCreate(BaseModel):
#     # Step 1: Name & Academic Initials
#     title: str = Field(..., example="Dr")
#     first_name: str = Field(..., min_length=2)
#     middle_name: Optional[str] = None
#     last_name: str = Field(..., min_length=2)
#     academic_degree: str = Field(..., example="PhD") 

#     # Step 2: Address
#     address_line1: str = Field(..., min_length=5)
#     address_line2: Optional[str] = None
#     city: str = Field(..., min_length=2)
#     postcode: str = Field(..., min_length=3)
#     country: str = Field(default="US")

#     # Step 3: Credentials & Licensing Board
#     professional_role: str = Field(..., example="Psychologist")
#     licensing_board: str = Field(..., example="California Board of Psychology")
#     registry_id: str = Field(..., description="Name or ID Number in Registry")
#     membership_type: str = Field(..., example="Accredited Member")

#     # Step 4: Regulatory (US Specific)
#     npi_number: str = Field(..., min_length=10, max_length=10)
#     license_number: str = Field(..., min_length=3)
#     license_state: str = Field(..., min_length=2, max_length=2)
    
#     # Generic Billing Token (could be from Stripe, PayPal, etc.)
#     billing_token: Optional[str] = Field(
#         None, 
#         description="Secure token from the payment gateway"
#     )
    
#     # Step 5: Account & Billing
#     email: EmailStr
#     password: str = Field(..., min_length=8)
#     # Note: payment_method_id comes from Stripe/Payment provider
#     payment_method_id: Optional[str] = None 

#     class Config:
#         from_attributes = True

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class ProviderRegistrationCreate(BaseModel):
    # Requested Fields
    first_name: str = Field(..., min_length=2)
    last_name: str = Field(..., min_length=2)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)
    phone_number: str = Field(..., description="Contact phone number")
    title: str = Field(..., example="Dr.", description="Profile Title")
    
    # Address Fields
    address: str = Field(..., min_length=5)
    state: str = Field(..., min_length=2, max_length=2)
    city: str = Field(..., min_length=2)
    zip_code: str = Field(..., min_length=5)
    
    # Professional/NPI Fields
    academic_degree: str = Field(..., example="PhD", description="Academics")
    npi_type: str = Field(..., example="NPI-1", description="NPI-1 (Individual) or NPI-2 (Org)")
    npi_number: str = Field(..., min_length=10, max_length=10)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v