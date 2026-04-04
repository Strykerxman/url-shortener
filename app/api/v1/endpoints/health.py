# -------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------
# This module provides a simple health check endpoint that verifies the API
# is running and responsive. Used for monitoring and load balancer health checks.
# -------------------------------------------------------

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from app.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import text

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    # Check DB connection
    try:
        db.execute(text("SELECT 1"))
        return {"status": "db healthy"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "detail": "Database connection error"},
        )
    
