from fastapi import APIRouter
from .endpoints.health import router as health_router
from .endpoints.urls import router as urls_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(urls_router, tags=["urls"])

__all__ = ["router"]