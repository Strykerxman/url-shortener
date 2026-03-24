# -------------------------------------------------------
# Rate Limiter
# -------------------------------------------------------
# Defines the shared Limiter instance used across the application.
# Defined here (not in main.py) to avoid circular imports: endpoints import
# limiter, main.py imports both endpoints and limiter.
#
# Limits are applied per client IP via get_remote_address.
# -------------------------------------------------------

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
