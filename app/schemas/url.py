# -------------------------------------------------------
# URL Schemas
# -------------------------------------------------------
# This module defines Pydantic models (schemas) for request and response validation
# in the FastAPI application. These schemas define the data structures exchanged
# between the API and clients, including validation rules and JSON serialization.
# -------------------------------------------------------

from pydantic import BaseModel

class URLBase(BaseModel):
    # Base schema for URL creation requests.
    # Contains only the target URL that the user wants to shorten.
    # Used as the input model for POST /url endpoint.
    target_url: str

class URL(URLBase):
    # Extended URL schema including computed fields from the database.
    # Inherits target_url from URLBase.
    # Used for internal data representation combining request and database data.
    # The Config class enables ORM mode to support conversion from SQLAlchemy models.
    is_active: bool  # Whether the shortened URL is currently active.
    clicks: int  # Number of times the shortened URL has been accessed.

    class Config:
        # Enable conversion from SQLAlchemy ORM models using from_attributes.
        # This allows Pydantic to populate the schema from ORM objects directly.
        from_attributes = True

class URLInfo(URL):
    # Complete URL information schema for API responses.
    # Inherits is_active and clicks from URL, and target_url from URLBase.
    # Includes the actual shortened and admin URLs to be returned to the client.
    url: str  # The public shortened URL (e.g., https://127.0.0.1:8000/ABCDEF).
    admin_url: str  # The admin URL for managing this shortened URL (e.g., https://127.0.0.1:8000/admin/ABCDEF_GHIJKLMN).