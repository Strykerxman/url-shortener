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


def create_key(length: int = 7) -> str:
    # Generate a random cryptographic key of specified length.
    # We increased default length from 5 to 7 characters.
    # REASONING: 62^5 (~916 million) is enumerable. 
    # 62^7 (~3.5 trillion) makes brute-force "guessing" impractical for a small service.
    chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def create_unique_key(db: Session) -> str:
    # Generate a random key and ensure it does not already exist in the database.
    # Collision probability is extremely low, but this function guarantees uniqueness.
    # SECURITY/LOGIC: We check ALL keys (even inactive/soft-deleted) to prevent
    # hijacking or unexpected behavior when reusing recycled IDs.
    key = create_key(length=7)
    # Keep generating new keys until a unique one is found across all records.
    while crud.get_any_db_url_by_key(db, key):
        key = create_key(length=7)
    return key
