from pydantic import SecretStr
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .core.config import get_settings
from .core.limiter import limiter
from .api.v1 import router


settings = get_settings()

app = FastAPI(
    title="URL Shortener API",
    description="An API for shortening URLs and managing them.",
    version="1.1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


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


app.include_router(router)