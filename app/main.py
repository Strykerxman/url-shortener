from contextlib import asynccontextmanager
from pydantic import SecretStr
from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from .core.config import get_settings
from .api.v1 import router
from .core.limiter import limiter
from .database.database import init_db
from .database.caching import init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup: Initialize resources.
    # This prevents side-effects at import time and follows IoC principles.
    init_db()
    init_redis()
    yield
    # Application shutdown cleanup (if needed) can go here.


app = FastAPI(
    title="URL Shortener API",
    description="An API for shortening URLs and managing them.",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

settings = get_settings()


@app.get("/")
async def read_root():
    return {"message": "Welcome to the URL Shortener API"}


app.include_router(router)