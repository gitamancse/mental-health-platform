from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ResponseItem(BaseModel):
    question_id: int
    option_index: int


class EvaluationRequest(BaseModel):
    questionnaire: str
    responses: List[ResponseItem]


class EvaluationResponse(BaseModel):
    patient_summary: str
    detailed_report: Dict[str, Any]