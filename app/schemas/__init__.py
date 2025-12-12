# -------------------------------------------------------
# Schemas Package Initializer
# -------------------------------------------------------
# This module serves as the public interface for the schemas package.
# It exports all Pydantic schema classes used for request/response validation
# throughout the FastAPI application.
# The __all__ export list explicitly declares which symbols are part of the
# package's public API.
# -------------------------------------------------------

from .url import URLBase, URLInfo, URL

__all__ = ["URLBase", "URLInfo", "URL"]