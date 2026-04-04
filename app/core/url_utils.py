# -------------------------------------------------------
# URL Utilities
# -------------------------------------------------------
# This module provides utility functions for constructing and formatting URLs
# used in API responses. It generates both public shortened URLs and admin URLs
# for management operations. Also contains centralized expiration logic.
# -------------------------------------------------------

from starlette.datastructures import URL
from sqlalchemy import or_

from app.core.config import Settings
from app import models, schemas
from datetime import datetime, timezone, timedelta
import re


def get_admin_info(db_url: models.URL, settings: Settings) -> schemas.URLInfo:
    # Construct and return URL information for administrative purposes.
    # This function creates both the public shortened URL and the admin endpoint info
    # by combining the application's base URL with the generated keys.
    # Parse the base URL from application settings.
    base_url = URL(settings.base_url)

    # Construct the public shortened URL using the short key.
    # Example: https://127.0.0.1:8000/ABCDEF
    db_url.url = str(base_url.replace(path=db_url.key))
    # NOTE: The secret_key is now transmitted via Authorization header, not URL path.
    # The admin_url field now contains the endpoint documentation instead of the secret.
    # SECURITY: Secrets in Authorization headers prevent leakage via logs, browser history,
    # and observability tooling. The secret_key field below contains the Bearer token.
    db_url.admin_url = f"Use Authorization header: Bearer {db_url.secret_key}"

    return db_url

def validate_url_key(key: str) -> bool:
    return key.isalnum() and len(key) == 7


def parse_time_to_expiry(spec: str) -> datetime:
    """Parse a human-friendly time-to-expiry string into a UTC datetime.

    Supported units:
    - h or hour(s): hours
    - min or minute(s): minutes
    - d or day(s): days
    - m or month(s): months (approximated as 30 days)

    Examples: '2h', '30min', '1d2h', '2m' (2 months => 60 days)
    Raises ValueError on invalid formats.
    """
    if not spec or not isinstance(spec, str):
        raise ValueError("time_to_expiry must be a non-empty string")

    spec = spec.strip().lower().replace(' ', '')
    pattern = re.compile(r"(\d+)(min|h|d|m)")
    matches = list(pattern.finditer(spec))
    if not matches:
        raise ValueError("Invalid time_to_expiry format")

    total = timedelta()
    for m in matches:
        value = int(m.group(1))
        unit = m.group(2)
        if unit == 'min':
            total += timedelta(minutes=value)
        elif unit == 'h':
            total += timedelta(hours=value)
        elif unit == 'd':
            total += timedelta(days=value)
        elif unit == 'm':
            # Treat months as 30 days
            total += timedelta(days=(value * 30))
        else:
            raise ValueError(f"Unsupported time unit: {unit}")

    if total > timedelta(days=365):
        raise ValueError("time_to_expiry cannot exceed 1 year (365 days)")
    if total < timedelta(minutes=1):
        raise ValueError("time_to_expiry must be a future duration")
    
    return datetime.now(timezone.utc) + total


def compute_expires_at(
    time_to_expiry: str = None,
    default_hours: int = 24
) -> datetime:
    """Centralized logic to compute the effective expiration datetime.
    
    Applies priority: explicit expires_at > relative time_to_expiry > default fallback.
    Normalizes all datetimes to UTC for consistent database storage.
    
    Args:
        time_to_expiry: Optional relative time string (e.g., '2h', '30min', '7d').
        default_hours: Default hours until expiration if neither above is provided.
    
    Returns:
        datetime in UTC timezone representing the effective expiration time.
    
    Raises:
        ValueError: If time_to_expiry format is invalid.
    """

    
    # Relative time-to-expiry string provided
    if time_to_expiry is not None:
        return parse_time_to_expiry(time_to_expiry)
    
    # Default fallback (24 hours by default)
    return datetime.now(timezone.utc) + timedelta(hours=default_hours)


def validate_expires_at(expires_at: datetime) -> None:
    """Validate that the expiration datetime is in the future.
    
    Args:
        expires_at: The expiration datetime to validate (should be in UTC).
    
    Raises:
        ValueError: If expires_at is not in the future.
    """
    assert expires_at.tzinfo == timezone.utc, "expires_at must be UTC-aware"
    now_utc = datetime.now(timezone.utc)
    if expires_at <= now_utc:
        raise ValueError(
            f"expires_at must be a future datetime (UTC). "
            f"Provided: {expires_at}, Current time: {now_utc}"
        )


def get_expiration_filter():
    """Return SQLAlchemy filter expression for non-expired URLs.
    
    Matches URLs that either have no expiration set (None) or whose expiration
    datetime is greater than the current UTC time.
    
    Returns:
        SQLAlchemy BinaryExpression for use in .filter() clauses.
    """
    now_utc = datetime.now(timezone.utc)
    return or_(models.URL.expires_at.is_(None), models.URL.expires_at > now_utc)
