# -------------------------------------------------------
# Database CRUD Operations
# -------------------------------------------------------
# This module provides all Create, Read, Update, Delete (CRUD) operations
# for URL objects in the database. It encapsulates database queries and
# persistence logic, serving as the data access layer for the application.
# All functions accept a SQLAlchemy Session object for database interaction
# and return ORM model instances or None.
# -------------------------------------------------------

from sqlalchemy.orm import Session
from sqlalchemy import update

from app.core import keygen
from app import schemas, models

def create_db_url(db: Session, url: schemas.URLBase) -> models.URL:
    # Generate a unique short key for the URL. This key is used in the shortened URL path.
    key = keygen.create_unique_key(db)
    # Create a secret key for administrative operations (delete/deactivate).
    # Combines the key with 8 additional random characters for security.
    secret_key = f"{key}_{keygen.create_key(8)}"

    # Create a new URL model instance with the provided target URL and generated keys.
    db_url = models.URL(
        target_url=url.target_url,
        key=key,
        secret_key=secret_key
    )
    # Add the new URL object to the session and persist it to the database.
    db.add(db_url)
    db.commit()
    # Refresh the object from the database to populate any auto-generated fields (e.g., id, timestamps).
    db.refresh(db_url)
    return db_url

def get_db_url_by_key(db: Session, url_key: str) -> models.URL:
    # Query the database for an active URL record matching the provided short key.
    # Returns the first matching URL object, or None if not found.
    return (
        db.query(models.URL)
        .filter(models.URL.key == url_key, models.URL.is_active)  # Filter by key and active status
        .first()  # Retrieve only the first result
    )

def get_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    # Query the database for an active URL record matching the provided secret key.
    # The secret key is required for sensitive operations like deletion or deactivation.
    # Returns the first matching URL object, or None if not found.
    return (
        db.query(models.URL)
        .filter(models.URL.secret_key == secret_key, models.URL.is_active)  # Filter by secret key and active status
        .first()  # Retrieve only the first result
    )

def add_click(db: Session, db_url: schemas.URL) -> models.URL:
    # Increment the click counter for a URL record, tracking how many times it has been accessed.
    db_url.clicks += 1
    # Persist the updated click count to the database.
    db.commit()
    # Refresh the object to ensure the latest state from the database.
    db.refresh(db_url)
    return db_url

def add_click_by_key(db: Session, url_key: str) -> models.URL:
    # Increment the click counter for a URL identified by its short key.
    # This function uses a SQL UPDATE statement for efficiency.
    stmt = (
        update(models.URL)
        .where(models.URL.key == url_key, models.URL.is_active)
        .values(clicks=models.URL.clicks + 1)
        .returning(models.URL)
    )
    result = db.execute(stmt)
    db.commit()
    return result.scalars().first()

def deactivate_db_url_by_secret_key(db: Session, secret_key: str) -> models.URL:
    # Retrieve the URL record using the provided secret key for authentication.
    db_url = get_db_url_by_secret_key(db, secret_key)
    # Only proceed if the URL record exists. This is a soft delete operation.
    if db_url:
        # Mark the URL as inactive instead of permanently deleting it.
        # This preserves the record for audit purposes while making it inaccessible.
        db_url.is_active = False
        # Persist the change to the database.
        db.commit()
        # Refresh the object to reflect the updated active status.
        db.refresh(db_url)
    # Return the updated URL object, or None if no matching record was found.
    return db_url    