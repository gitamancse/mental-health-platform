from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.modules.provider.schemas.registration_schema import ProviderRegistrationCreate
# 1. Update import to the Class
from app.modules.provider.services.registration_service import RegistrationService
from app.db.session import get_db

router = APIRouter(prefix="/provider")

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_provider(
    registration_data: ProviderRegistrationCreate,
    db: Session = Depends(get_db)
):
    """
    Endpoint to register a new provider.
    Performs Luhn check, NPI registry verification, and duplicate checks.
    """
    # 2. Convert Pydantic model to dictionary
    # Use .model_dump() for Pydantic v2, or .dict() for Pydantic v1
    data_dict = registration_data.model_dump() 

    # 3. Await the asynchronous service method
    return await RegistrationService.create_registration(db, data_dict)