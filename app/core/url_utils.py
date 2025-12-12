# -------------------------------------------------------
# URL Utilities
# -------------------------------------------------------
# This module provides utility functions for constructing and formatting URLs
# used in API responses. It generates both public shortened URLs and admin URLs
# for management operations.
# -------------------------------------------------------

from starlette.datastructures import URL

from app.core.config import get_settings
from app import models, schemas


def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    # Construct and return URL information for administrative purposes.
    # This function creates both the public shortened URL and the admin URL
    # by combining the application's base URL with the generated keys.
    settings = get_settings()
    # Parse the base URL from application settings.
    base_url = URL(settings.base_url)

    # Construct the public shortened URL using the short key.
    # Example: https://127.0.0.1:8000/ABCDEF
    db_url.url = str(base_url.replace(path=db_url.key))
    # Construct the admin URL using the secret key for authentication.
    # Example: https://127.0.0.1:8000/admin/ABCDEF_GHIJKLMN
    db_url.admin_url = str(base_url.replace(path=f"admin/{db_url.secret_key}"))
    
    return db_url