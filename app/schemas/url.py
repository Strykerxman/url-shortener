# -------------------------------------------------------
# URL Schemas
# -------------------------------------------------------
# This module defines Pydantic models (schemas) for request and response validation
# in the FastAPI application. These schemas define the data structures exchanged
# between the API and clients, including validation rules and JSON serialization.
# -------------------------------------------------------

from pydantic import BaseModel, ConfigDict, Field, field_serializer
from datetime import datetime, timezone
from typing import Optional


class URLBase(BaseModel):
    # Base schema for URL creation requests.
    # Contains only the target URL that the user wants to shorten.
    # Used as the input model for POST /url endpoint.
    target_url: str
    # Allow clients to provide a relative time-to-expiry string such as '2h', '30min', '7d', or '2m' (months).
    time_to_expiry: Optional[str] = Field(default="24h", exclude=True)


class URL(URLBase):
    # Extended URL schema including computed fields from the database.
    # Inherits target_url and expires_at from URLBase.
    # Used for internal data representation combining request and database data.
    model_config = ConfigDict(from_attributes=True)
    expires_at: Optional[datetime] = None  # Optional expiration datetime for the URL.
    is_active: bool  # Whether the shortened URL is currently active.
    clicks: int  # Number of times the shortened URL has been accessed.

    @field_serializer("expires_at", when_used="json")
    def serialize_expires_at(self, value: Optional[datetime]):
        if value is None:
            return None
        # Emit local timezone in API JSON for client-facing readability.
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone().isoformat()


class URLInfo(URL):
    # Complete URL information schema for API responses.
    # Inherits is_active, clicks, expires_at from URL, and target_url from URLBase.
    # Includes the actual shortened and admin URLs to be returned to the client.
    url: str  # The public shortened URL (e.g., https://127.0.0.1:8000/ABCDEF).
    admin_url: str  # The admin URL for managing this shortened URL (e.g., https://127.0.0.1:8000/admin/ABCDEF_GHIJKLMN).
