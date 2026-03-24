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
import asyncio

from app.core import logging
from app.core.limiter import limiter
from app import schemas
from app.core.config import get_settings
from app.core.url_utils import get_admin_info, validate_url_key
from app.database import crud, get_db, get_redis

import validators

# Create a router instance to register all URL-related endpoints.
router = APIRouter()


@router.get("/{url_key}")
@limiter.limit("60/minute")
async def forward_to_target_url(
    url_key: str,
    request: Request,
    db_session: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
):
    # Validate the URL key format before proceeding.
    if not validate_url_key(url_key):
        logging.raise_not_found(request)
    # Try cache first with a short timeout; on any cache error/timeouts, fall back to DB.
    try:
        cached_url = await redis_client.get(url_key)
        if cached_url:
            if db_url := crud.add_click_by_key(db_session, url_key):

                return RedirectResponse(cached_url)
            await redis_client.delete(url_key)
            logging.raise_not_found(request)
    except Exception as e:
        logging.logger.warning(
            "Redis get failed for key=%s; falling back to DB. Error: %s",
            url_key,
            e,
            exc_info=True,
        )
    # DB fallback
    if db_url := crud.add_click_by_key(db_session, url_key):
        await _safe_redis_set(redis_client, db_url)
        return RedirectResponse(db_url.target_url)

    # Not found
    logging.raise_not_found(request)


@router.post("/url", response_model=schemas.URLInfo)
@limiter.limit("10/minute")
async def create_url(
    url: schemas.URLBase,
    request: Request,
    db_session: Session = Depends(get_db),
    redis_client: Redis = Depends(get_redis),
):
    # Validate the provided target URL format using the validators library.
    # The URL must include http:// or https:// protocol.
    if not validators.url(url.target_url):
        logging.raise_bad_request(
            message="Your provided URL is not valid. **Must include http:// or https://**"
        )

    # Create a new URL record in the database with auto-generated keys.
    db_url = crud.create_db_url(db_session, url)

    # Set the shortened URL key for the response (public short link).
    db_url.url = db_url.key

    # Set the admin secret key for the response (used for delete/update operations).
    db_url.admin_url = db_url.secret_key

    await _safe_redis_set(redis_client, db_url)
    # Construct and return a Pydantic response while the DB session is still
    # open to avoid lazy-loading or additional DB access during serialization.
    # For Pydantic v2 use `model_validate` (schemas.Config sets from_attributes=True).
    try:
        return schemas.URLInfo.model_validate(db_url)
    except AttributeError:
        # Fallback for older Pydantic versions (from_orm)
        return schemas.URLInfo.from_orm(db_url)


@router.get(
    "/admin/{secret_key}", name="administration info", response_model=schemas.URLInfo
)
async def get_url_info(
    secret_key: str,
    request: Request,
    db_session: Session = Depends(get_db),
    settings=Depends(get_settings),
):
    # Retrieve the URL record using the provided secret key for authentication.
    if db_url := crud.get_db_url_by_secret_key(db_session, secret_key):
        # URL found: return formatted admin information including statistics.
        url_info = get_admin_info(db_url, settings)
        return url_info
    else:
        # URL not found or inactive: raise a 404 error with detailed logging.
        logging.raise_not_found(request)


@router.delete("/admin/{secret_key}", name="delete url")
async def delete_url(
    secret_key: str, request: Request, db_session: Session = Depends(get_db)
):
    # Retrieve and deactivate the URL record using the provided secret key for authentication.
    if _ := crud.deactivate_db_url_by_secret_key(db_session, secret_key):
        # URL successfully deactivated (soft delete): return confirmation message.
        return {"detail": f"URL with secret key {secret_key} has been deactivated."}
    else:
        # URL not found or already inactive: raise a 404 error with detailed logging.
        logging.raise_not_found(request)


async def _safe_redis_set(redis_client: Redis, db_url):
    try:
        await asyncio.wait_for(
            redis_client.set(db_url.key, db_url.target_url, ex=(3600 * 24)),
            timeout=0.75,
        )
    except asyncio.TimeoutError:
        logging.logger.warning("Timed out setting Redis key=%s", db_url.key)
    except Exception:
        logging.logger.exception("Error setting Redis key=%s", db_url.key)
