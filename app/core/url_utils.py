# -------------------------------------------------------
# URL Utilities
# -------------------------------------------------------
# This module provides utility functions for constructing and formatting URLs
# used in API responses. It generates both public shortened URLs and admin URLs
# for management operations.
# -------------------------------------------------------

from starlette.datastructures import URL

from app.core.config import Settings
from app import models, schemas


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
