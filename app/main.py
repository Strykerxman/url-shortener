from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .core.limiter import limiter
from .api.v1 import router


app = FastAPI(
    title="URL Shortener API",
    description="An API for shortening URLs and managing them.",
    version="1.0.0",
)

# Attach the rate limiter to app state so slowapi can read it per-request.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
async def read_root():
    return {"message": "Welcome to the URL Shortener API"}


app.include_router(router)