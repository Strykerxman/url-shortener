# -------------------------------------------------------
# Redis Caching Client
# -------------------------------------------------------
# Lightweight Redis helpers used by endpoints for read-through caching.
# - Non-blocking timeouts ensure cache issues never slow the API.
# - Missing/failed Redis is treated as non-fatal; the app falls back to DB.
# -------------------------------------------------------
import redis.asyncio as redis
import asyncio
from app.core import logging
from app.core.config import get_settings

settings = get_settings()

# Initialize connection pool as None to prevent side-effects during import.
# This follows Inversion of Control: resources are managed, not global.
pool = None


def init_redis():
    """
    Initialize the Redis connection pool.
    Separates resource allocation from module loading.
    """
    global pool
    if pool is None:
        pool = redis.ConnectionPool(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
        logging.logger.info(
            "Redis connection pool initialized for %s:%d", 
            settings.redis_host, 
            settings.redis_port
        )


async def get_redis() -> redis.Redis:
    """
    Dependency injection for Redis clients.
    Ensures the pool is initialized before yielding a client.
    """
    if pool is None:
        init_redis()
        
    client: redis.Redis = redis.Redis(connection_pool=pool)
    try:
        await client.ping()
    except Exception as e:
        logging.logger.warning(
            "Redis ping failed during connection; continuing without cache. Error: %s",
            e,
            exc_info=True,
        )
    return client


async def safe_redis_set(client: redis.Redis, key: str, value: str, ex: int | None):
    # Set a cache entry with an expiry, using a tight timeout to avoid blocking requests.
    # Any error or timeout is logged; callers should not rely on cache writes succeeding.
    try:
        await asyncio.wait_for(client.set(key, value, ex=ex), timeout=0.75)
    except asyncio.TimeoutError:
        logging.logger.warning("Timed out setting Redis key=%s", key)
    except Exception:
        logging.logger.exception("Error setting Redis key=%s", key)
