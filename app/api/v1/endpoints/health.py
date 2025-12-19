# -------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------
# This module provides a simple health check endpoint that verifies the API
# is running and responsive. Used for monitoring and load balancer health checks.
# -------------------------------------------------------

from fastapi import APIRouter
from app.database import get_db
from sqlalchemy.orm import Session

# Create a router instance to register endpoints with the API.
router = APIRouter()

@router.get("/health")
async def health_check():
    # Check DB connection
    try:
        db: Session = None
        async with get_db() as db:
            # Simple query to verify DB connectivity
            db.execute("SELECT 1")
    except Exception as e:
        return {"status": "unhealthy", "detail": f"Database connection error: {str(e)}"}
    return {"status": "healthy"}