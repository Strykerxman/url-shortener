# -------------------------------------------------------
# Health Check Endpoint
# -------------------------------------------------------
# This module provides a simple health check endpoint that verifies the API
# is running and responsive. Used for monitoring and load balancer health checks.
# -------------------------------------------------------

from fastapi import APIRouter

# Create a router instance to register endpoints with the API.
router = APIRouter()

@router.get("/health")
async def health_check():
    # Return a simple status response indicating the API is operational.
    # This endpoint is used by monitoring systems and load balancers to verify
    # that the service is running and healthy.
    return {"status": "ok"}