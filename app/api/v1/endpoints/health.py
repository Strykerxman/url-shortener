# -------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------
# This module provides a simple health check endpoint that verifies the API
# is running and responsive. Used for monitoring and load balancer health checks.
# -------------------------------------------------------

from fastapi import APIRouter
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
async def health_check():
    # Check DB connection
    try:
        db: Session = next(get_db())
        db.execute(text("SELECT 1"))
    except Exception as e:
        return {"status": "unhealthy", "detail": f"Database connection error: {str(e)}"}
    return {"status": "db healthy"}