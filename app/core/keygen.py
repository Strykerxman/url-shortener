# -------------------------------------------------------
# Key Generation Utilities
# -------------------------------------------------------
# This module provides functions for generating secure random keys used in URL shortening.
# It includes both general-purpose key generation and logic to ensure uniqueness
# by checking against existing keys in the database.
# Keys consist of uppercase letters and digits for URL-safe representation.
# -------------------------------------------------------

import secrets
import string

from app.database import crud
from sqlalchemy.orm import Session

def create_key(length: int = 5) -> str:
    # Generate a random cryptographic key of specified length.
    # Uses uppercase letters (A-Z) and digits (0-9) for URL-safe representation.
    # The secrets module provides cryptographically strong random generation.
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))

def create_unique_key(db: Session) -> str:
    # Generate a random key and ensure it does not already exist in the database.
    # Collision probability is extremely low, but this function guarantees uniqueness
    # by querying the database and regenerating if a collision is found.
    key = create_key()
    # Keep generating new keys until a unique one is found.
    while crud.get_db_url_by_key(db, key):
        key = create_key()
    return key    