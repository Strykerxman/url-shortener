# -------------------------------------------------------
# Models Package Initializer
# -------------------------------------------------------
# This module serves as the public interface for the models package.
# It exports the URL ORM model class for use by other modules.
# The __all__ export list explicitly declares which symbols are part of the
# package's public API.
# -------------------------------------------------------

from .url import URL

__all__ = ["URL"]