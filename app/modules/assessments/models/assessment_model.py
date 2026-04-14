import uuid
from sqlalchemy import Column, String, Float, JSON, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base


class RawEvent(Base):
    __tablename__ = "raw_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(80))
    payload = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class AssessmentSubmission(Base):
    __tablename__ = "assessment_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(64))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assessment_id = Column(String(200))
    score = Column(Float)
    result_json = Column(JSON)
    ip_address = Column(String)
    user_agent = Column(String)
    submitted_at = Column(DateTime, default=datetime.utcnow)