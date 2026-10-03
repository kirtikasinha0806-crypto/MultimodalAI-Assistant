from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db, is_postgres
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])

@router.get("")
def health_check(db: Session = Depends(get_db)):
    """Check API status, database health, and AI configuration."""
    db_status = "healthy"
    db_type = "postgresql+pgvector" if is_postgres else "sqlite_fallback"
    
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy ({str(e)})"

    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "database": {
            "status": db_status,
            "type": db_type,
            "is_postgres": is_postgres
        },
        "gemini": {
            "configured": bool(settings.GEMINI_API_KEY),
            "primary_model": settings.PRIMARY_MODEL,
            "embedding_model": settings.EMBEDDING_MODEL
        }
    }
