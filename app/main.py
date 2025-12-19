from pydantic import SecretStr
from fastapi import FastAPI
from .core.config import get_settings
from .api.v1 import router


app = FastAPI(
    title="URL Shortener API",
    description="An API for shortening URLs and managing them.",
    version="1.0.0",
)
app.include_router(router)
settings = get_settings()

@app.get("/")
async def read_root():
    return {"message": "Welcome to the URL Shortener API"}

@app.get("/settings")
async def read_settings():
    return {
        "database_url": SecretStr(settings.sqlalchemy_database_url),
        "base_url": settings.base_url,
        "debug": settings.debug,
        "env_name": settings.env_name,
    }