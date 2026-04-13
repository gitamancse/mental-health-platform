from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
import app.db.models 

# Import routers
from app.modules.auth.routers.auth_router import auth_router
from app.modules.assessments.routers.assessment_router import router as assessment_router

from app.db.session import engine
from app.db.base import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mental Health Platform API")

# Include routers
app.include_router(auth_router, prefix="/api", tags=["Authentication"])

app.include_router(assessment_router)

@app.get("/")
def root():
    return {"message": "API Running"}