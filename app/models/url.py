# -------------------------------------------------------
# URL Model
# -------------------------------------------------------
# This module defines the URL ORM model using SQLAlchemy.
# The URL class represents a shortened URL record in the database with fields for
# the target URL, generated short key, secret key for admin operations, and click tracking.
# Each URL record is immutable after creation except for the is_active flag (soft delete)
# and the clicks counter (analytics).
# -------------------------------------------------------

from app.database.database import Base
from sqlalchemy import Column, Integer, String, Boolean

class URL(Base):
    # Table name in the database.
    __tablename__ = "urls"

    # Primary key identifier for the URL record.
    id = Column(Integer, primary_key=True)
    # Short key used in the public shortened URL path. Must be unique.
    # Indexed for fast lookups during redirects.
    key = Column(String, unique=True, index=True)
    # Secret key used for authentication in admin operations (view info, delete).
    # Must be unique and indexed for fast lookups.
    secret_key = Column(String, unique=True, index=True)
    # The original target URL that this shortened URL redirects to.
    # Indexed to support analytics queries.
    target_url = Column(String, index=True)
    # Flag indicating whether this URL is active (True) or deactivated (False).
    # Defaults to True. Set to False when the URL is deleted (soft delete pattern).
    is_active = Column(Boolean, default=True)
    # Counter tracking the number of times this shortened URL has been accessed.
    # Incremented each time a redirect occurs, used for analytics.
    clicks = Column(Integer, default=0)

    def __repr__(self):
        # Return a string representation of the URL object for debugging and logging.
        return f"<URL(id={self.id}, key={self.key}, target_url={self.target_url}, is_active={self.is_active}, clicks={self.clicks})>"
    