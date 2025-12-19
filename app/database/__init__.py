# -------------------------------------------------------
# Database Package Initializer
# -------------------------------------------------------
# This module serves as the public interface for the database package.
# It exposes the get_db dependency injection function for use by other modules
# in the application (primarily FastAPI route dependencies).
# The __all__ export list explicitly declares which symbols are part of the
# package's public API.
# -------------------------------------------------------

from .database import get_db
from .caching import get_redis

__all__ = ["get_db", "get_redis"]