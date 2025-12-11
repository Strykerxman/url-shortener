from .core import get_settings
from .database import init_db
from .api.v1 import health_router, urls_router
from fastapi import FastAPI

app = FastAPI(
    title="URL Shortener API",
    description="An API for shortening URLs and managing them.",
    version="1.0.0",
)

init_db()

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(urls_router, prefix="/api/v1", tags=["urls"])

settings = get_settings()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the URL Shortener API"}

@app.get("/settings")
async def read_settings():
    return {
        "database_url": settings.database_url,
        "debug": settings.debug,
        "host": settings.host,
        "port": settings.port,
        "env_name": settings.env_name,
    }

