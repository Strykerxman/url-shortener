# -------------------------------------------------------
# Rate Limiter
# -------------------------------------------------------
# Shared Limiter instance used across the application.
# Defined here to avoid circular imports between main.py and endpoint modules.
# -------------------------------------------------------

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
