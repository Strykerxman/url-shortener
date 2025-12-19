# -------------------------------------------------------
# URL Shortener API Endpoints
# -------------------------------------------------------
# This module defines all REST API endpoints for URL shortening operations.
# It provides functionality to create shortened URLs, redirect to target URLs,
# view URL statistics, and delete (deactivate) shortened URLs.
# All endpoints integrate with the database CRUD layer for persistence and
# use dependency injection to obtain database sessions.
# -------------------------------------------------------

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from redis.asyncio import Redis

from app.core import logging
from app import schemas
from app.core.url_utils import get_admin_info
from app.database import crud, get_db, get_redis

import validators

# Create a router instance to register all URL-related endpoints.
router = APIRouter()

@router.get("/{url_key}")
async def forward_to_target_url(url_key: str, request: Request, db_session: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    # First, attempt to retrieve the target URL from Redis cache for performance.
    try:
        if cached_url := await redis_client.get(url_key):
            # URL found in cache: increment the click counter for analytics tracking.
            if db_url := crud.get_db_url_by_key(db_session, url_key):
                crud.add_click(db_session, db_url)

            return RedirectResponse(cached_url)
    except Exception as e:
        # Log cache failures but fall back to the database so redirects still work.
        logging.logger.error("Failed to retrieve URL from Redis: %s", str(e))

    # Attempt to retrieve the URL record from the database using the provided short key.
    if db_url := crud.get_db_url_by_key(db_session, url_key):        
        # URL found: increment the click counter for analytics tracking.
        crud.add_click(db_session, db_url)
        
        return RedirectResponse(db_url.target_url)
    else:
        # URL not found or inactive: raise a 404 error with detailed logging.
        logging.raise_not_found(request)

@router.post("/url", response_model=schemas.URLInfo)
async def create_url(url: schemas.URLBase, db_session: Session = Depends(get_db), redis_client: Redis = Depends(get_redis)):
    # Validate the provided target URL format using the validators library.
    # The URL must include http:// or https:// protocol.
    if not validators.url(url.target_url):
        logging.raise_bad_request(message="Your provided URL is not valid. **Must include http:// or https://**")

    # Create a new URL record in the database with auto-generated keys.
    db_url = crud.create_db_url(db_session, url)
    
    # Set the shortened URL key for the response (public short link).
    db_url.url = db_url.key

    # Set the admin secret key for the response (used for delete/update operations).
    db_url.admin_url = db_url.secret_key

    try:
        await redis_client.set(db_url.key, db_url.target_url, ex=(3600 * 24))  # Cache for 24 hours (ex is in seconds)
    except Exception as e:
        logging.raise_cache_error(message=f"Failed to cache URL in Redis: {str(e)}")
        return
    # Return the created URL with both public and admin URLs.
    return db_url

@router.get("/admin/{secret_key}", name="administration info", response_model=schemas.URLInfo)
async def get_url_info(secret_key: str, request: Request, db_session: Session = Depends(get_db)):
    # Retrieve the URL record using the provided secret key for authentication.
    if db_url := crud.get_db_url_by_secret_key(db_session, secret_key):
        # URL found: return formatted admin information including statistics.
        return get_admin_info(db_url)
    else:
        # URL not found or inactive: raise a 404 error with detailed logging.
        logging.raise_not_found(request)


@router.delete("/admin/{secret_key}", name="delete url")
async def delete_url(secret_key: str, request: Request, db_session: Session = Depends(get_db)):
    # Retrieve and deactivate the URL record using the provided secret key for authentication.
    if db_url := crud.deactivate_db_url_by_secret_key(db_session, secret_key):
        # URL successfully deactivated (soft delete): return confirmation message.
        return {"detail": f"URL with secret key {secret_key} has been deactivated."}
    else:
        # URL not found or already inactive: raise a 404 error with detailed logging.
        logging.raise_not_found(request)
