from fastapi import FastAPI
from app.db.session import engine
from app.db.base import Base
import app.db.models 

# Import routers
from app.modules.auth.routers.auth_router import auth_router

from app.db.session import engine
from app.db.base import Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mental Health Platform API")

# Include routers
app.include_router(auth_router, prefix="/api", tags=["Authentication"])

@app.get("/")
def root():
    return {"message": "API Running"}