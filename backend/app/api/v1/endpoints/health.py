from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.db.session import get_db

router = APIRouter()


@router.get("/live")
def liveness():
    """Liveness probe - confirms the process is running."""
    return {"status": "alive"}


@router.get("/ready")
def readiness(db: Session = Depends(get_db)):
    """Readiness probe - confirms the app can serve traffic (DB is reachable)."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        return {
            "status": "not_ready",
            "database": str(exc),
            "version": settings.VERSION,
        }

    return {
        "status": "ready",
        "database": db_status,
        "version": settings.VERSION,
    }
