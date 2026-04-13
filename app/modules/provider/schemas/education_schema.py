# app/modules/provider/schemas/education_schema.py
from typing import Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EducationCreate(BaseModel):
    degree: str
    institution: str
    field_of_study: str
    graduation_year: Optional[int] = None
    license_type: Optional[str] = None


class EducationResponse(BaseModel):
    id: UUID
    degree: str
    institution: str
    field_of_study: str
    graduation_year: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)