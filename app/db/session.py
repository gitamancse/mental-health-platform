from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Engine
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=True
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ✅ For scripts / manual use
def get_db_session():
    return SessionLocal()

# ✅ For FastAPI dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()