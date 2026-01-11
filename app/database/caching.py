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

pool = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)
logging.logger.info(
    "Redis connection pool created for %s:%d", settings.redis_host, settings.redis_port
)


async def get_redis() -> redis.Redis:
    # Provides a Redis client from the shared connection pool.
    # Ping is best-effort: failures are logged and ignored to keep the API responsive.
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
