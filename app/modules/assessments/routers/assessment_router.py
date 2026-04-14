from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.modules.assessments.schemas.assessment_schema import EvaluationRequest
from app.modules.assessments.services.assessment_service import (
    get_questionnaire_service,
    evaluate_service
)
from app.db.session import get_db

router = APIRouter(prefix="/assessments", tags=["Assessments"])


@router.get("/questionnaire/{disorder_name}")
def get_questionnaire(disorder_name: str):
    return get_questionnaire_service(disorder_name)


@router.post("/evaluate")
def evaluate(request: EvaluationRequest, db: Session = Depends(get_db)):
    return evaluate_service(db, request)