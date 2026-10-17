"""Health and operational diagnostic endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.ai.parser import get_ai_service_status
from app.config import settings
from app.db.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    """Health status, database connectivity, and active AI provider check."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    ai_status = get_ai_service_status()

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "app": settings.PROJECT_NAME,
        "tagline": settings.TAGLINE,
        "version": settings.VERSION,
        "database": db_status,
        "ai_provider": ai_status["provider"],
        "ai_model": ai_status["model"],
    }

